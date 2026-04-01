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

# --- CARREGAMENTO DO DRIVE ---
@st.cache_data(ttl=600)
def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    file_id = '13Ekq0dn38mZ99Zz_V5zYmW7og3hS24cN' 
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar base do Drive: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos (Filtros Avançados)")
    st.caption("CORE ESSENCE - Inteligência em Dados de Convênios")

    df_base = carregar_dados_drive()

    if not df_base.empty:
        # Tratamento inicial de valores
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        # --- 1º FILTRO: PESQUISA TEXTUAL (OCUPA A LINHA TODA) ---
        st.markdown("### 🔍 Painel de Filtros")
        termo = st.text_input("1. Pesquisa na Base (Favorecido, Órgão ou Objeto):").upper()
        
        # --- 2º, 3º e 4º FILTROS: ANO, ESTADO E CIDADE (EM COLUNAS) ---
        c1, c2, c3 = st.columns(3)
        
        with c1:
            col_ano = next((c for c in df_base.columns if 'ANO' in c), None)
            anos = ["Todos"] + sorted(df_base[col_ano].dropna().unique().astype(str).tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", anos)

        with c2:
            col_uf = next((c for c in df_base.columns if 'UF' in c or 'ESTADO' in c), None)
            ufs = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", ufs)

        with c3:
            col_mun = next((c for c in df_base.columns if 'MUNICIPIO' in c or 'CIDADE' in c), None)
            cidades = ["Todos"] + sorted(df_base[col_mun].dropna().unique().astype(str).tolist()) if col_mun else ["Todos"]
            filtro_mun = st.selectbox("4. Cidade:", cidades)

        # --- LÓGICA DE FILTRAGEM COMBINADA ---
        df_filtrado = df_base
        
        if termo:
            mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]
        
        if filtro_ano != "Todos":
            df_filtrado = df_filtrado[df_filtrado[col_ano].astype(str) == filtro_ano]
            
        if filtro_uf != "Todos":
            df_filtrado = df_filtrado[df_filtrado[col_uf].astype(str) == filtro_uf]
            
        if filtro_mun != "Todos":
            df_filtrado = df_filtrado[df_filtrado[col_mun].astype(str) == filtro_mun]

        # --- EXIBIÇÃO DE RESULTADOS ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_filtrado.columns:
            total = df_filtrado['VALOR_NUM'].sum()
            k1.metric("Total Identificado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Registros Encontrados", len(df_filtrado))

        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("Conectando à base de dados no Drive...")

if __name__ == "__main__":
    exibir_radar()
