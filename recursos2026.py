import streamlit as st
import pandas as pd
import gdown
import os

# --- FUNÇÃO DE LIMPEZA MONETÁRIA ---
def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0":
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except:
        return 0.0

def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        if len(df.columns) <= 1:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip')

        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # --- TRATAMENTO DO ANO ---
        col_data = next((c for c in df.columns if 'DATA' in c or 'DT' in c), None)
        if col_data:
            df['ANO_FILTRO'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.year
            if df['ANO_FILTRO'].isnull().all():
                df['ANO_FILTRO'] = df[col_data].astype(str).str.extract(r'(\d{4})')
            df = df.dropna(subset=['ANO_FILTRO'])
            df['ANO_FILTRO'] = df['ANO_FILTRO'].astype(float).astype(int).astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar base: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos - Core Essence")
    
    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- MAPEAMENTO DE COLUNAS ---
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = 'ANO_FILTRO' if 'ANO_FILTRO' in df_base.columns else None
        col_uf = 'UF' if 'UF' in df_base.columns else None
        
        # BUSCA REFINADA PARA CIDADE: Evita colunas de CÓDIGO e busca NOMES
        col_mun = next((c for c in df_base.columns if any(x in c for x in ['NOME_MUN', 'MUNICIPIO', 'CIDADE', 'LOCALIDADE']) and 'COD' not in c), None)

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        st.markdown("### 🔍 Painel de Filtros")
        termo = st.text_input("1. Busca Geral (Favorecido/Objeto):").upper()
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", opcoes_ano)

        with c2:
            opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", opcoes_uf)

        with c3:
            # Força a coluna de cidade a ser texto para evitar números com .0
            if col_mun:
                lista_cidades = ["Todos"] + sorted(df_base[col_mun].dropna().astype(str).unique().tolist())
            else:
                lista_cidades = ["Todos"]
            filtro_mun = st.selectbox("4. Cidade:", lista_cidades)

        # --- FILTRAGEM ---
        df_f = df_base.copy()
        if termo:
            mask = df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_f = df_f[mask]
        if filtro_ano != "Todos":
            df_f = df_f[df_f[col_ano] == filtro_ano]
        if filtro_uf != "Todos":
            df_f = df_f[df_f[col_uf].astype(str) == filtro_uf]
        if filtro_mun != "Todos":
            df_f = df_f[df_f[col_mun].astype(str) == filtro_mun]

        # --- DASHBOARD ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_f.columns:
            k1.metric("Total Filtrado", f"R$ {df_f['VALOR_NUM'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Registros", len(df_f))

        st.dataframe(df_f, use_container_width=True)
    else:
        st.info("Carregando base...")

if __name__ == "__main__":
    exibir_radar()
