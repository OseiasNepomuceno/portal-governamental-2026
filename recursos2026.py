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
        
        df = pd.read_excel(caminho_final) if planilha.endswith('.xlsx') else pd.read_csv(caminho_final, sep=';', encoding='latin1')

        # --- LIMPEZA DE VALORES (Resolve o erro do 'f') ---
        def limpar_valor(valor):
            if isinstance(valor, str):
                valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            return pd.to_numeric(valor, errors='coerce')

        colunas_valor = ['VALOR CONVÊNIO', 'VALOR LIBERADO']
        for col in colunas_valor:
            if col in df.columns:
                df[col] = df[col].apply(limpar_valor).fillna(0)

        # Filtro de Ano 2026
        if 'DATA PUBLICAÇÃO' in df.columns:
            df['DATA PUBLICAÇÃO'] = pd.to_datetime(df['DATA PUBLICAÇÃO'], errors='coerce')
            df = df[df['DATA PUBLICAÇÃO'].dt.year == 2026]
            
        return df
            
    except Exception as e:
        st.error(f"Erro interno no Radar: {e}")
        return None

# --- INTERFACE ---
st.title("🔍 Radar de Recursos 2026")
st.markdown("---")

df_radar = carregar_dados_drive()

if df_radar is not None:
    col_mun = 'NOME MUNICÍPIO'
    col_valor = 'VALOR CONVÊNIO'
    col_liberado = 'VALOR LIBERADO'

    if col_mun in df_radar.columns:
        # Filtro de Município
        lista_municipios = ["Todos"] + sorted(df_radar[col_mun].dropna().unique().tolist())
        municipio_sel = st.selectbox("Selecione a Cidade:", lista_municipios)
        
        df_final = df_radar.copy()
        if municipio_sel != "Todos":
            df_final = df_radar[df_radar[col_mun] == municipio_sel]

        # --- CARDS COM FORMATAÇÃO SEGURA ---
        total_convenio = float(df_final[col_valor].sum())
        total_liberado = float(df_final[col_liberado].sum())
        
        c1, c2, c3 = st.columns(3)
        # Formatação usando f-string padrão para evitar o erro anterior
        c1.metric("Total em Convênios", f"R$ {total_convenio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c2.metric("Total Liberado", f"R$ {total_liberado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c3.metric("Qtd. de Projetos", len(df_final))

        st.markdown("---")
        st.write(f"### Detalhamento: {municipio_sel}")
        st.dataframe(df_final, use_container_width=True)
