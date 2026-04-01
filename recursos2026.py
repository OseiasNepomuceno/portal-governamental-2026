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

# --- CARREGAMENTO DO DRIVE VIA SECRETS ---
@st.cache_data(ttl=600)
def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    
    # BUSCANDO DO SECRETS (Certifique-se que o nome lá é exatamente 'file_id_convenios')
    file_id = st.secrets.get("file_id_convenios")
    
    if not file_id:
        st.error("🚨 Erro: 'file_id_convenios' não encontrado nos Secrets do Streamlit.")
        return pd.DataFrame()

    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Testando separadores comuns: tenta ';' primeiro, se der erro tenta ','
        try:
            df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
            if len(df.columns) <= 1: # Se vier só uma coluna, o separador provavelmente está errado
                df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip')
        except:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip')

        # Limpeza radical nos nomes das colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # AJUDA PARA VOCÊ: Mostra as colunas encontradas no rodapé (depois você pode tirar)
        # st.write("Colunas detectadas:", list(df.columns))
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar base do Drive: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos (Filtros Avançados)")
    
    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- BUSCA DE COLUNAS POR PALAVRA-CHAVE ---
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = next((c for c in df_base.columns if 'ANO' in c), None)
        # Tenta UF, ESTADO ou SIGLA
        col_uf = next((c for c in df_base.columns if any(x in c for x in ['UF', 'ESTADO', 'SIGLA'])), None)
        # Tenta MUNICIPIO, CIDADE, LOCALIDADE ou NOME_M
        col_mun = next((c for c in df_base.columns if any(x in c for x in ['MUNICIPIO', 'CIDADE', 'LOCALIDADE', 'MUNIC'])), None)

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        st.markdown("### 🔍 Painel de Controle de Filtros")
        
        termo = st.text_input("1. Pesquisa Geral (Nome, Objeto ou Órgão):").upper()
        
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

        # --- FILTRAGEM ---
        df_filtrado = df_base
        
        if termo:
            mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]
        
        if filtro_ano != "Todos" and col_ano:
            df_filtrado = df_filtrado[df_filtrado[col_ano].astype(str) == filtro_ano]
            
        if filtro_uf != "Todos" and col_uf:
            df_filtrado = df_filtrado[df_filtrado[col_uf].astype(str) == filtro_uf]
            
        if filtro_mun != "Todos" and col_mun:
            df_filtrado = df_filtrado[df_filtrado[col_mun].astype(str) == filtro_mun]

        # --- RESULTADOS ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_filtrado.columns:
            total = df_filtrado['VALOR_NUM'].sum()
            k1.metric("Total Identificado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Total de Registros", len(df_filtrado))

        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("Aguardando carregamento dos dados do Drive via Secrets...")

if __name__ == "__main__":
    exibir_radar()
