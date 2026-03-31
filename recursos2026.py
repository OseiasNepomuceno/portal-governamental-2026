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
@st.cache_data(ttl=60)
def buscar_dados_governo(codigo_ibge, ano, mes):
    # Tenta ler a chave de 3 formas diferentes (Segurança máxima)
    chave = st.secrets.get("chave-api-dados") or \
            st.secrets.get("chave-api-dados") or \
            st.secrets.get("default", {}).get("chave-api-dados")

    if not chave:
        # Se mesmo assim não achar, vamos listar o que o Streamlit ESTÁ vendo
        chaves_vistas = list(st.secrets.to_dict().keys())
        st.error(f"🚨 O Streamlit não encontrou a chave. Ele só consegue ver estas chaves: {chaves_vistas}")
        return []

    token = str(chave).strip().replace('"', '').replace("'", "")
    
    # Formato MM/AAAA conforme a regra da CGU
    data_formatada = f"{mes}/{ano}"
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/transferencias/por-municipio"
    
    headers = {
        "chave-api-dados": token,
        "Accept": "application/json",
        "User-Agent": "CoreEssence-Radar/1.0"
    }
    
    params = {"codigoIbge": codigo_ibge, "mesAno": data_formatada, "pagina": 1}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=25)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 403:
            st.error("🚫 Erro 403: Acesso Negado pelo Governo. Verifique a autorização no portal.")
            return []
        else:
            st.error(f"Erro {res.status_code} na API do Governo.")
            return []
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
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
