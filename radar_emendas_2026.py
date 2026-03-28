import streamlit as st
import gdown
import pandas as pd
import zipfile
import os

# --- CONFIGURAÇÃO DE ACESSO ---
FILE_ID = '19cZvPOcHSDUY9PVs22XxwVmSPB5OTh-k'
url = f'https://drive.google.com/uc?id={FILE_ID}'
zip_output = 'emendas_radar.zip'
extract_path = 'emendas_extraidas'

@st.cache_data(ttl=3600, show_spinner="Aguarde, carregando Radar de Emendas...")
def carregar_emendas_drive():
    try:
        if not os.path.exists(zip_output):
            gdown.download(url, zip_output, quiet=True, fuzzy=True)
        
        with zipfile.ZipFile(zip_output, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        arquivos = os.listdir(extract_path)
        planilha = [f for f in arquivos if f.endswith('.csv')][0]
        caminho_final = os.path.join(extract_path, planilha)
        
        # Leitura com tratamento de erro para tipos de dados
        df = pd.read_csv(caminho_final, sep=';', encoding='latin1', low_memory=False)

        # --- LIMPEZA DE DADOS (IMPEDIR ERRO DE FLOAT vs STR) ---
        # Convertemos colunas de filtro para String e removemos valores nulos
        cols_texto = ['NOME_PARLAMENTAR', 'SIGLA_PARTIDO', 'OBJETO_PROPOSTA']
        for col in cols_texto:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', 'NÃO INFORMADO')

        # Limpeza de Valores Financeiros
        cols_financeiras = ['VALOR_REPASSE_PROPOSTA', 'VALOR_EMPENHADO', 'VALOR_REEMBOLSADO']
        for col in cols_financeiras:
            if col in df.columns:
                # Remove R$, pontos e troca vírgula por ponto
                df[col] = df[col].astype(str).str.replace('R\$ ', '', regex=True).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Erro ao carregar emendas: {e}")
        return None

# --- INTERFACE ---
st.title("🏛️ Radar de Emendas Parlamentares")
st.caption("CORE ESSENCE - Consultoria e Estratégia Governamental")
st.markdown("---")

df_emendas = carregar_emendas_drive()

if df_emendas is not None:
    # --- FILTROS POLÍTICOS (CORRIGIDOS) ---
    col1, col2 = st.columns(2)
    
    with col1:
        # O list(map(str, ...)) garante que o sorted não compare float com str
        lista_parlamentares = sorted(df_emendas['NOME_PARLAMENTAR'].unique().tolist())
        autor_sel = st.selectbox("Selecione o Parlamentar:", ["Todos"] + lista_parlamentares)
        
    df_filt = df_emendas.copy()
    if autor_sel != "Todos":
        df_filt = df_filt[df_filt['NOME_PARLAMENTAR'] == autor_sel]

    with col2:
        lista_partidos = sorted(df_filt['SIGLA_PARTIDO'].unique().tolist())
        partido_sel = st.selectbox("Filtrar por Partido:", ["Todos"] + lista_partidos)

    if partido_sel != "Todos":
        df_filt = df_filt[df_filt['SIGLA_PARTIDO'] == partido_sel]

    # --- MÉTRICAS ---
    total_emenda = float(df_filt['VALOR_REPASSE_PROPOSTA'].sum())
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total em Emendas", f"R$ {total_emenda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    m2.metric("Parlamentares", len(df_filt['NOME_PARLAMENTAR'].unique()))
    m3.metric("Qtd. Propostas", len(df_filt))

    # --- GRÁFICO ---
    st.subheader("📊 Distribuição por Partido (Valor)")
    if not df_filt.empty:
        chart_data = df_filt.groupby('SIGLA_PARTIDO')['VALOR_REPASSE_PROPOSTA'].sum().sort_values(ascending=False)
        st.bar_chart(chart_data)

    st.markdown("---")
    st.dataframe(df_filt, use_container_width=True)
