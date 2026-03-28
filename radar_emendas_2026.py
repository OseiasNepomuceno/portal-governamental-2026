import streamlit as st
import gdown
import pandas as pd
import zipfile
import os

def executar(): # ADICIONE ESTA LINHA
    
    # TODO O RESTANTE DO SEU CÓDIGO AQUI COM UM "TAB" PARA DENTRO
    
    # --- CONFIGURAÇÃO DE ACESSO ---
    # Ele vai buscar o ID_EMENDAS que você salvou no Secrets
    FILE_ID = st.secrets["ID_EMENDAS"]
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
            
            # Leitura com tratamento para caracteres especiais no início (BOM)
            df = pd.read_csv(caminho_final, sep=';', encoding='latin1', low_memory=False)
            
            # Limpeza básica dos nomes das colunas (remove caracteres invisíveis)
            df.columns = [c.replace('Ï»¿', '').strip().upper() for c in df.columns]
                    
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
        # Nomes exatos baseados no seu retorno
        col_parl = 'NOME_PARLAMENTAR'
        col_valor = 'VALOR_REPASSE_PROPOSTA_EMENDA'
        col_emenda = 'NR_EMENDA'
        col_tipo = 'TIPO_PARLAMENTAR'
    
        # --- LIMPEZA DE DADOS ---
        df_emendas[col_parl] = df_emendas[col_parl].astype(str).replace('nan', 'NÃO INFORMADO')
        
        def limpar_financa(v):
            if isinstance(v, str):
                v = v.replace('R$', '').replace('.', '').replace(',', '.').strip()
            return pd.to_numeric(v, errors='coerce')
        
        df_emendas[col_valor] = df_emendas[col_valor].apply(limpar_financa).fillna(0)
    
        # --- FILTROS ---
        c1, c2 = st.columns(2)
        with c1:
            lista_parl = sorted(df_emendas[col_parl].unique().tolist())
            autor_sel = st.selectbox("Selecione o Parlamentar:", ["Todos"] + lista_parl)
        
        df_filt = df_emendas.copy()
        if autor_sel != "Todos":
            df_filt = df_filt[df_filt[col_parl] == autor_sel]
    
        with c2:
            lista_tipos = sorted(df_filt[col_tipo].dropna().unique().tolist())
            tipo_sel = st.selectbox("Filtrar por Tipo (Deputado/Senador):", ["Todos"] + lista_tipos)
    
        if tipo_sel != "Todos":
            df_filt = df_filt[df_filt[col_tipo] == tipo_sel]
    
        # --- MÉTRICAS ---
        t_emenda = float(df_filt[col_valor].sum())
        m1, m2, m3 = st.columns(3)
        m1.metric("Total em Emendas", f"R$ {t_emenda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("Nº de Emendas", len(df_filt[col_emenda].unique()))
        m3.metric("Propostas Geradas", len(df_filt))
    
        # --- GRÁFICO ---
        st.subheader("📊 Volume de Recursos por Parlamentar")
        if not df_filt.empty:
            # Se selecionou um parlamentar, mostra o detalhe, senão mostra o ranking dos top 10
            if autor_sel == "Todos":
                chart_data = df_filt.groupby(col_parl)[col_valor].sum().sort_values(ascending=False).head(10)
            else:
                chart_data = df_filt.groupby(col_emenda)[col_valor].sum().sort_values(ascending=False)
            st.bar_chart(chart_data)
    
        st.markdown("---")
        st.write("### Lista de Propostas Disponíveis")
        st.dataframe(df_filt, use_container_width=True)
