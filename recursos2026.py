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
    file_id = '1UXFvhI3WlYuYidPbbZdojA3jyINmb-L6' 
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Lendo com separador ';' e tratando acentos
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        # Limpa espaços extras nos nomes das colunas e coloca em MAIÚSCULO
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos (Filtros Inteligentes)")
    
    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- DETECTIVE DE COLUNAS (Busca por palavras-chave) ---
        # Procura colunas que contenham essas palavras no nome
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = next((c for c in df_base.columns if 'ANO' in c), None)
        col_uf = next((c for c in df_base.columns if 'UF' in c or 'ESTADO' in c or 'SIGLA' in c), None)
        col_mun = next((c for c in df_base.columns if 'MUNICIPIO' in c or 'CIDADE' in c or 'LOCALIDADE' in c), None)

        # Limpeza de valores para os KPIs
        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        st.markdown("### 🔍 Painel de Filtros")
        
        # 1. Filtro de Texto Livre
        termo = st.text_input("1. Pesquisa Geral (Favorecido ou Objeto):").upper()
        
        # Filtros em colunas
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if col_ano:
                lista_anos = ["Todos"] + sorted(df_base[col_ano].dropna().unique().astype(str).tolist(), reverse=True)
            else:
                lista_anos = ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", lista_anos)

        with c2:
            if col_uf:
                lista_ufs = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist())
            else:
                lista_ufs = ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", lista_ufs)

        with c3:
            if col_mun:
                lista_cidades = ["Todos"] + sorted(df_base[col_mun].dropna().unique().astype(str).tolist())
            else:
                lista_cidades = ["Todos"]
            filtro_mun = st.selectbox("4. Cidade:", lista_cidades)

        # --- APLICAÇÃO DOS FILTROS ---
        df_filtrado = df_base
        
        if termo:
            # Filtra em todas as colunas de texto
            mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]
        
        if filtro_ano != "Todos" and col_ano:
            df_filtrado = df_filtrado[df_filtrado[col_ano].astype(str) == filtro_ano]
            
        if filtro_uf != "Todos" and col_uf:
            df_filtrado = df_filtrado[df_filtrado[col_uf].astype(str) == filtro_uf]
            
        if filtro_mun != "Todos" and col_mun:
            df_filtrado = df_filtrado[df_filtrado[col_mun].astype(str) == filtro_mun]

        # --- EXIBIÇÃO ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_filtrado.columns:
            total = df_filtrado['VALOR_NUM'].sum()
            k1.metric("Total Identificado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Registros", len(df_filtrado))

        st.dataframe(df_filtrado, use_container_width=True)
        
        # Dica técnica se as colunas não forem encontradas
        if not col_uf or not col_mun:
            st.info("💡 Dica: Se os filtros de Estado/Cidade estão vazios, verifique se o CSV tem colunas chamadas UF e MUNICIPIO.")

    else:
        st.warning("⚠️ Base de dados não encontrada ou vazia no Drive.")
