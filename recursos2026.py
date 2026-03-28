import streamlit as st
import gdown
import pandas as pd
import zipfile
import os

# --- CONFIGURAÇÃO ---
FILE_ID = '1p_ihzkzi-osypEKjOaBy8LKz5rR9Kqtc'
url = f'https://drive.google.com/uc?id={FILE_ID}'
zip_output = 'dados_radar.zip'
extract_path = 'dados_extraidos'

@st.cache_data(ttl=3600)
def carregar_dados_drive():
    try:
        if not os.path.exists(zip_output):
            gdown.download(url, zip_output, quiet=True, fuzzy=True)
        
        with zipfile.ZipFile(zip_output, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        arquivos = os.listdir(extract_path)
        planilha = [f for f in arquivos if f.endswith(('.xlsx', '.csv'))][0]
        caminho_final = os.path.join(extract_path, planilha)
        
        # Lendo apenas as colunas que importam para economizar memória (Performance)
        df = pd.read_excel(caminho_final) if planilha.endswith('.xlsx') else pd.read_csv(caminho_final, sep=';', encoding='latin1')

        # --- PADRONIZAÇÃO DE COLUNAS (O SEGREDO DO ERRO) ---
        # Transformamos todos os nomes de colunas para maiúsculas e sem acentos internamente para facilitar
        df.columns = [str(c).upper().strip() for c in df.columns]
        
        # --- FILTRO ANO 2026 ---
        colunas_ano = ['ANO', 'ANO_CONVENIO', 'EXERCICIO', 'ANO_PROPOSTA']
        col_ano_encontrada = next((c for c in colunas_ano if c in df.columns), None)
        
        if col_ano_encontrada:
            df = df[df[col_ano_encontrada] == 2026]
            
        return df
            
    except Exception as e:
        st.error(f"Erro interno no Radar: {e}")
        return None

# --- INTERFACE ---
st.title("🔍 Radar de Recursos 2026")
st.markdown("---")

df_radar = carregar_dados_drive()

if df_radar is not None:
    # Identificar a coluna de Município dinamicamente
    colunas_mun = ['MUNICÍPIO', 'MUNICIPIO', 'NM_MUNICIPIO', 'NOME_MUNICIPIO', 'MUNICIPIO_BENEFICIARIO']
    col_mun_real = next((c for c in colunas_mun if c in df_radar.columns), None)

    if col_mun_real:
        st.success(f"✅ Filtro 2026 Ativo: {len(df_radar)} registros processados.")
        
        # Filtro de Município
        lista_municipios = ["Todos"] + sorted(df_radar[col_mun_real].dropna().unique().tolist())
        municipio_sel = st.selectbox("Selecione a Cidade para análise:", lista_municipios)
        
        df_final = df_radar.copy()
        if municipio_sel != "Todos":
            df_final = df_radar[df_radar[col_mun_real] == municipio_sel]
        
        # Exibição
        st.write(f"### Dados de: {municipio_sel}")
        st.dataframe(df_final, use_container_width=True)
    else:
        st.error("❌ Não encontramos uma coluna de 'Município' na planilha. Verifique o cabeçalho.")
        st.write("Colunas encontradas:", list(df_radar.columns))

# Título do Módulo
st.title("🔍 Radar de Recursos 2026")
st.markdown("### Monitoramento de Convênios e Repasses Federais")

df, erro = carregar_dados_drive()

if erro:
    st.error(erro)
elif df is not None:
    st.success("Dados carregados com sucesso da nuvem!")
    # ... aqui continua o restante dos seus filtros ...


# 1. Configuração da Página
st.set_page_config(page_title="Radar Transferegov 2026", layout="wide")

st.title("🔍 Radar de Recursos 2026")
st.subheader("Monitoramento de Convênios e Repasses Federais")


# 2. Função de Carregamento
def carregar_dados(caminho_zip):
    if not os.path.exists(caminho_zip):
        return None, "Arquivo ZIP não encontrado na pasta."
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as z:
            arquivos_csv = [f for f in z.namelist() if f.endswith('.csv')]
            if not arquivos_csv: return None, "Nenhum CSV dentro do ZIP."
            with z.open(arquivos_csv[0]) as f:
                df = pd.read_csv(f, sep=None, engine='python', encoding='latin1')
                df.columns = df.columns.str.strip().str.upper()
                return df, None
    except Exception as e:
        return None, str(e)


# 3. Execução
CAMINHO_ARQUIVO = "20260313_Convenios.zip"
df, erro = carregar_dados(CAMINHO_ARQUIVO)

if erro:
    st.error(f"❌ Erro: {erro}")
elif df is not None:
    # --- MAPEAMENTO SEGURO DE COLUNAS ---
    # Se não achar pelo nome, pega pela posição provável
    col_uf = 'UF_PROPONENTE' if 'UF_PROPONENTE' in df.columns else df.columns[1]
    col_mun = 'MUNICICIPIO_PROPONENTE' if 'MUNICICIPIO_PROPONENTE' in df.columns else df.columns[3]
    col_valor = 'VALOR_GLOBAL_CONV' if 'VALOR_GLOBAL_CONV' in df.columns else df.columns[5]
    col_objeto = 'OBJETO_PROPOSTA' if 'OBJETO_PROPOSTA' in df.columns else df.columns[4]

    # --- LIMPEZA DE MOEDA (CRUCIAL) ---
    df[col_valor] = df[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)

    # --- FILTROS LATERAIS ---
    st.sidebar.header("⚙️ Filtros")
    lista_uf = sorted(df[col_uf].unique().astype(str))
    uf_sel = st.sidebar.multiselect("Estados:", lista_uf, default=["SP", "MG"] if "SP" in lista_uf else lista_uf[:1])
    valor_min = st.sidebar.number_input("Valor Mínimo (R$):", min_value=0, value=100000)
    busca = st.sidebar.text_input("Palavra-chave no Objeto:")

    # --- APLICAR FILTROS ---
    mask = (df[col_uf].isin(uf_sel)) & (df[col_valor] >= valor_min)
    if busca:
        mask = mask & (df[col_objeto].str.contains(busca, case=False, na=False))

    df_filtrado = df[mask].copy()

    # --- DASHBOARD DE MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    total = df_filtrado[col_valor].sum()
    c1.metric("Convênios", len(df_filtrado))
    c2.metric("Total em Recursos", f"R$ {total:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    c3.metric("Municípios", df_filtrado[col_mun].nunique())

    # --- GRÁFICO ---
    if not df_filtrado.empty:
        st.markdown("### 📊 Top 10 Municípios (Volume de Recurso)")
        grafico_data = df_filtrado.groupby(col_mun)[col_valor].sum().sort_values(ascending=False).head(10)
        st.bar_chart(grafico_data)

    # --- TABELA E DOWNLOAD ---
    st.markdown("### 📋 Detalhes dos Convênios")
    st.dataframe(df_filtrado[[col_uf, col_mun, col_valor, col_objeto]], use_container_width=True)

    csv = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 Baixar Relatório", data=csv, file_name="radar_2026.csv", mime="text/csv")
