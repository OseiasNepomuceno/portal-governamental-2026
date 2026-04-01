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

# --- CARREGAMENTO DO DRIVE (SEM API GOVERNO) ---
@st.cache_data(ttl=600)
def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    # ID do seu arquivo no Drive
    file_id = '13Ekq0dn38mZ99Zz_V5zYmW7og3hS24cN' 
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Lendo o CSV do Drive
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar base do Drive: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos (Base Drive)")
    st.caption("CORE ESSENCE - Inteligência em Dados Internos")

    df_base = carregar_dados_drive()

    if not df_base.empty:
        # Tratamento de valores
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        # Interface de Filtros
        st.markdown("### 🔍 Pesquisa na Base")
        termo = st.text_input("Filtrar por Favorecido, Órgão ou Objeto:").upper()
        
        df_filtrado = df_base
        if termo:
            mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_filtrado = df_base[mask]

        # KPIs
        c1, c2 = st.columns(2)
        if 'VALOR_NUM' in df_filtrado.columns:
            total = df_filtrado['VALOR_NUM'].sum()
            c1.metric("Total Identificado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Registros", len(df_filtrado))

        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("Carregando dados do Google Drive...")
