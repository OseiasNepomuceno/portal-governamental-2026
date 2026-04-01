import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0":
        return 0.0
    try:
        # Limpeza robusta para R$ 1.234,56 -> 1234.56
        v = str(v).upper().replace('R$', '').replace(' ', '').strip()
        if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
        elif ',' in v: v = v.replace(',', '.')
        return float(v)
    except:
        return 0.0

@st.cache_data(ttl=600)
def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    if not file_id:
        st.error("🚨 file_id_convenios não definido nos Secrets.")
        return pd.DataFrame()
    
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Tenta ler com separador ; (padrão Brasil)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        if len(df.columns) <= 1: # Se falhar, tenta vírgula
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip')
        
        # Limpa nomes das colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos - Core Essence")
    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- LINHA DE DEBUG (Apague após resolver o problema) ---
        # st.write("Colunas lidas do seu arquivo:", list(df_base.columns))

        # --- MAPEAMENTO AMPLIADO DE COLUNAS ---
        # Tenta encontrar qualquer coluna que lembre o campo
        col_valor = next((c for c in df_base.columns if any(x in c for x in ['VALOR', 'PRECO', 'MONTANTE'])), None)
        col_ano = next((c for c in df_base.columns if any(x in c for x in ['ANO', 'EXERCICIO', 'DATA', 'PERIODO'])), None)
        col_uf = next((c for c in df_base.columns if any(x in c for x in ['UF', 'ESTADO', 'SIGLA', 'SGL'])), None)
        col_mun = next((c for c in df_base.columns if any(x in c for x in ['MUNICIPIO', 'CIDADE', 'LOCALIDADE', 'MUNIC'])), None)

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        st.markdown("### 🔍 Filtros de Auditoria")
        termo = st.text_input("1. Busca Geral:").upper()
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            # Se encontrar a coluna de ANO, gera a lista, senão mantém "Todos"
            opcoes_ano = ["Todos"] + sorted(df_base[col_ano].dropna().unique().astype(str).tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", opcoes_ano)

        with c2:
            # Se encontrar a coluna de UF, gera a lista, senão mantém "Todos"
            opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", opcoes_uf)

        with c3:
            opcoes_mun = ["Todos"] + sorted(df_base[col_mun].dropna().unique().astype(str).tolist()) if col_mun else ["Todos"]
            filtro_mun = st.selectbox("4. Cidade:", opcoes_mun)

        # --- FILTRAGEM COMBINADA ---
        df_f = df_base.copy()
        if termo:
            df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)]
        if filtro_ano != "Todos":
            df_f = df_f[df_f[col_ano].astype(str) == filtro_ano]
        if filtro_uf != "Todos":
            df_f = df_f[df_f[col_uf].astype(str) == filtro_uf]
        if filtro_mun != "Todos":
            df_f = df_f[df_f[col_mun].astype(str) == filtro_mun]

        # --- DASHBOARD ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_f.columns:
            k1.metric("Total Filtrado", f"R$ {df_f['VALOR_NUM'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Nº de Registros", len(df_f))

        st.dataframe(df_f, use_container_width=True)
    else:
        st.info("Aguardando carregamento da base 20260320_Convenios.csv...")

if __name__ == "__main__":
    exibir_radar()
