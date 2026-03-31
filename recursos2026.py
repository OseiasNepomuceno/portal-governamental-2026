import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar de Recursos | Core Essence", page_icon="🛰️", layout="wide")

# --- FUNÇÃO DE BUSCA NA API (PURA E DIRETA) ---
@st.cache_data(ttl=3600)
def buscar_dados_governo(codigo_ibge, mes_ano):
    # 1. Busca a chave e remove TUDO o que não for letra ou número
    chave_raw = st.secrets.get("PORTAL_TRANSPARENCIA_KEY")
    
    if not chave_raw:
        st.error("🚨 Chave não encontrada nos Secrets!")
        return []

    # Limpeza total: remove espaços, aspas e quebras de linha
    token_limpo = "".join(chave_raw.split()).replace('"', '').replace("'", "")
    
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/transferencias/por-municipio"
    
    # Header exatamente como solicitado no e-mail: "chave-api-dados"
    headers = {
        "chave-api-dados": token_limpo,
        "Accept": "application/json"
    }
    
    params = {
        "codigoIbge": codigo_ibge, 
        "mesAno": mes_ano, 
        "pagina": 1
    }
    
    try:
        # Aumentamos o timeout para 30 segundos
        res = requests.get(url, headers=headers, params=params, timeout=30)
        
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 403:
            st.error(f"🚫 Erro 403 (Acesso Negado)")
            st.info(f"O servidor do Governo reconheceu a chave finalizada em '...{token_limpo[-4:]}', mas negou o acesso.")
            st.markdown("---")
            st.warning("👉 **Ação Necessária:** Tente entrar no site da API novamente e veja se há algum aviso de 'Chave Suspensa' ou se o limite diário foi atingido (mesmo sem usar).")
            return []
        else:
            st.error(f"Erro {res.status_code} vindo do Governo.")
            return []
    except Exception as e:
        st.error(f"Falha de conexão: {e}")
        return []

def executar():
    st.title("🛰️ Radar de Recursos Governamentais")
    st.caption("CORE ESSENCE - Inteligência em Dados Públicos (Via API Federal)")

    with st.sidebar:
        st.header("🔑 Painel do Consultor")
        plano = st.selectbox("Seu Plano:", ["Start", "Professional", "Enterprise"])
        st.divider()
        st.header("📍 Parâmetros de Busca")
        # Presidente Prudente como padrão
        ibge = st.text_input("Código IBGE do Município", value="3541406")
        
        # Sugestão: Testar com Janeiro/Fevereiro de 2026 para garantir que há dados
        ano = st.selectbox("Ano", [2026, 2025, 2024], index=0)
        mes = st.selectbox("Mês", [f"{i:02d}" for i in range(1, 13)], index=1) # index 1 = Fevereiro
        
        btn_radar = st.button("Rastrear Agora")

    if btn_radar:
        data_ref = f"{ano}{mes}"
        with st.spinner(f"Consultando base federal de {mes}/{ano}..."):
            resultados = buscar_dados_governo(ibge, data_ref)
            
            if resultados:
                df = pd.DataFrame(resultados)
                total = df['valor'].sum()
                
                st.success(f"✅ Sucesso! Conexão estabelecida com a API do Governo.")
                
                c1, c2 = st.columns(2)
                c1.metric("Total Identificado", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                c2.metric("Repasses", len(df))

                st.subheader("📋 Relatório Detalhado")
                st.dataframe(df[['tipoTransferencia', 'favorecido', 'valor', 'origemRecurso']], use_container_width=True)
            else:
                st.info(f"Nenhum repasse encontrado para {mes}/{ano}. Tente o mês anterior (Fevereiro/2026 ou Janeiro/2026).")
