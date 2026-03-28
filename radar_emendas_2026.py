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
        
        # Leitura flexível
        df = pd.read_csv(caminho_final, sep=';', encoding='latin1', low_memory=False)

        # Padroniza todos os nomes de colunas para MAIÚSCULAS para facilitar a busca
        df.columns = [str(c).upper().strip() for c in df.columns]
                
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
    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    # Identifica o nome real da coluna de Parlamentar
    col_parl = next((c for c in ['NOME_PARLAMENTAR', 'NM_PARLAMENTAR', 'NOME_PARL'] if c in df_emendas.columns), None)
    # Identifica o nome real da coluna de Partido
    col_partido = next((c for c in ['SIGLA_PARTIDO', 'SG_PARTIDO', 'PARTIDO', 'SIGLA_PARTIDO_PARLAMENTAR'] if c in df_emendas.columns), None)
    # Identifica a coluna de Valor
    col_valor = next((c for c in ['VALOR_REPASSE_PROPOSTA', 'VL_REPASSE', 'VALOR_EMENDA'] if c in df_emendas.columns), None)

    if col_parl and col_partido and col_valor:
        
        # --- LIMPEZA DE DADOS ---
        df_emendas[col_parl] = df_emendas[col_parl].astype(str).replace('nan', 'NÃO INFORMADO')
        df_emendas[col_partido] = df_emendas[col_partido].astype(str).replace('nan', 'NÃO INFORMADO')
        
        # Limpeza de Valores Financeiros
        def limpar_financa(v):
            if isinstance(v, str):
                v = v.replace('R$', '').replace('.', '').replace(',', '.').strip()
            return pd.to_numeric(v, errors='coerce')
        
        df_emendas[col_valor] = df_emendas[col_valor].apply(limpar_financa).fillna(0)

        # --- FILTROS POLÍTICOS ---
        c1, c2 = st.columns(2)
        with c1:
            lista_parl = sorted(df_emendas[col_parl].unique().tolist())
            autor_sel = st.selectbox("Selecione o Parlamentar:", ["Todos"] + lista_parl)
        
        df_filt = df_emendas.copy()
        if autor_sel != "Todos":
            df_filt = df_filt[df_filt[col_parl] == autor_sel]

        with c2:
            lista_part = sorted(df_filt[col_partido].unique().tolist())
            part_sel = st.selectbox("Filtrar por Partido:", ["Todos"] + lista_part)

        if part_sel != "Todos":
            df_filt = df_filt[df_filt[col_partido] == part_sel]

        # --- MÉTRICAS ---
        t_emenda = float(df_filt[col_valor].sum())
        m1, m2, m3 = st.columns(3)
        m1.metric("Total em Emendas", f"R$ {t_emenda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("Parlamentares", len(df_filt[col_parl].unique()))
        m3.metric("Qtd. Propostas", len(df_filt))

        # --- GRÁFICO ---
        st.subheader("📊 Distribuição por Partido (Valor)")
        if not df_filt.empty:
            chart_data = df_filt.groupby(col_partido)[col_valor].sum().sort_values(ascending=False)
            st.bar_chart(chart_data)

        st.markdown("---")
        st.dataframe(df_filt, use_container_width=True)
    else:
        st.error("❌ Não conseguimos identificar as colunas de dados. Verifique os nomes na planilha.")
        st.write("Colunas encontradas:", list(df_emendas.columns))
