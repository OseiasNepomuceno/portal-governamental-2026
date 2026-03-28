import streamlit as st
import gdown
import pandas as pd
import zipfile
import os

# ID do seu arquivo que você enviou
FILE_ID = '1p_ihzkzi-osypEKjOaBy8LKz5rR9Kqtc'
url = f'https://drive.google.com/uc?id={FILE_ID}'
zip_output = 'dados_radar.zip'
extract_path = 'dados_extraidos'

@st.cache_data(ttl=3600)
def carregar_e_extrair_dados():
    try:
        # 1. Baixa o arquivo ZIP do seu Drive
        gdown.download(url, zip_output, quiet=True, fuzzy=True)
        
        # 2. Extrai o conteúdo do ZIP
        with zipfile.ZipFile(zip_output, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 3. Localiza o arquivo .xlsx ou .csv dentro da pasta extraída
        arquivos = os.listdir(extract_path)
        planilha = [f for f in arquivos if f.endswith(('.xlsx', '.csv'))][0]
        caminho_final = os.path.join(extract_path, planilha)
        
        # 4. Lê os dados
        if planilha.endswith('.xlsx'):
            return pd.read_excel(caminho_final)
        else:
            return pd.read_csv(caminho_final, sep=';', encoding='latin1')
            
    except Exception as e:
        st.error(f"Erro ao processar o Radar: {e}")
        return None

# Execução
df = carregar_e_extrair_dados()

if df is not None:
    st.success(f"✅ Radar de Recursos Ativo! ({len(df)} registros encontrados)")
    st.dataframe(df.head(10)) # Mostra os primeiros 10 para teste


# --- INTERFACE ---
st.title("🔍 Radar de Recursos 2026")
df, erro = carregar_dados_drive()

if erro:
    st.error(f"⚠️ {erro}")
    st.info("Dica: Verifique se o arquivo no Drive está como 'Qualquer pessoa com o link'.")
elif df is not None:
    st.success(f"✅ {len(df)} registros carregados com sucesso!")
    # Aqui entra o seu código de filtros (st.selectbox, etc)

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
