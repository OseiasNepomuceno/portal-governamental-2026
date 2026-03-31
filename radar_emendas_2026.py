import streamlit as st
import pandas as pd
import gdown
import zipfile
import os
import requests

# --- FUNÇÃO 1: BUSCA NA API (PARA ANOS ANTERIORES) ---
@st.cache_data(ttl=3600)
def buscar_emendas_api(ano):
    chave = st.secrets.get("chave-api-dados")
    if not chave: return []
    token = str(chave).strip().replace('"', '').replace("'", "")
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
    headers = {"chave-api-dados": token, "Accept": "application/json"}
    params = {"ano": ano, "pagina": 1}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=20)
        return res.json() if res.status_code == 200 else []
    except: return []

# --- FUNÇÃO 2: BUSCA NO DRIVE (PARA 2026 ATUALIZÁVEL) ---
@st.cache_data(ttl=600, show_spinner="Sincronizando base manual do Transferegov...")

def carregar_emendas_drive():
    FILE_ID = st.secrets.get("ID_EMENDAS")
    if not FILE_ID: 
        st.error("ID_EMENDAS não encontrado nos Secrets.")
        return None
    
    # URL configurada para download direto de arquivo CSV
    url = f'https://drive.google.com/uc?export=download&id={FILE_ID}'
    output_csv = 'dados_2026_direto.csv'
    
    try:
        # Remove versão antiga para garantir dados novos
        if os.path.exists(output_csv): 
            os.remove(output_csv)
        
        # Download do CSV
        gdown.download(url, output_csv, quiet=False, fuzzy=True)
        
        if not os.path.exists(output_csv):
            st.error("Não foi possível baixar o arquivo. Verifique o ID e as permissões.")
            return None

        # Leitura do CSV (Ajustado para o padrão do governo: latin1 e ponto-e-vírgula)
        df = pd.read_csv(output_csv, sep=';', encoding='latin1', low_memory=False)
        
        # Limpeza e Padronização
        df.columns = [c.replace('ï»¿', '').strip().upper() for c in df.columns]
        df['ANO_REFERENCIA'] = 2026
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar CSV do Drive: {e}")
        return None

def executar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    st.caption("CORE ESSENCE - Inteligência Híbrida (API Gov + Transferegov)")
    st.markdown("---")

    with st.sidebar:
        st.header("📍 Filtros")
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
        btn_buscar = st.button("🔍 Rastrear Recursos")

    if btn_buscar:
        df_final = pd.DataFrame()
        
        if ano_sel == 2026:
            # BUSCA NO SEU ARQUIVO MANUAL DO DRIVE
            df_final = carregar_emendas_drive()
            col_valor = 'VALOR_REPASSE_PROPOSTA_EMENDA'
            col_autor = 'NOME_PARLAMENTAR'
        else:
            # BUSCA NA API OFICIAL
            dados = buscar_emendas_api(ano_sel)
            if dados:
                df_final = pd.DataFrame(dados)
                col_valor = 'valorEmpenhado'
                col_autor = 'nomeAutor'

        if df_final is not None and not df_final.empty:
            # --- LIMPEZA DE VALORES ---
            df_final[col_valor] = df_final[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_final[col_valor] = pd.to_numeric(df_final[col_valor], errors='coerce').fillna(0)

            # --- MÉTRICAS ---
            total = df_final[col_valor].sum()
            st.metric(f"Total em Emendas ({ano_sel})", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            # --- GRÁFICO ---
            st.subheader(f"📊 Top Autores - {ano_sel}")
            chart_data = df_final.groupby(col_autor)[col_valor].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data)
            
            st.dataframe(df_final, use_container_width=True)
        else:
            st.info("Aguardando atualização de dados para este período.")

if __name__ == "__main__":
    executar()
