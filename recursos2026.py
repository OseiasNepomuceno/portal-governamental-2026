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
@st.cache_data(ttl=3600)
def buscar_dados_governo(codigo_ibge, mes_ano):
    # Tenta pegar a chave. Se não achar, avisa o usuário de forma amigável
    try:
        chave = st.secrets.get("PORTAL_TRANSPARENCIA_KEY")
        if not chave:
            st.error("🚨 Chave da API não encontrada nos Secrets!")
            return []
            
        url = "https://api.portaldatransparencia.gov.br/api-de-dados/transferencias/por-municipio"
        headers = {"chave-api-dados": chave}
        
        all_results = []
        pagina = 1
        
        while pagina <= 3:
            params = {"codigoIbge": codigo_ibge, "mesAno": mes_ano, "pagina": pagina}
            res = requests.get(url, headers=headers, params=params, timeout=15)
            if res.status_code == 200:
                dados = res.json()
                if not dados: break
                all_results.extend(dados)
                pagina += 1
            else:
                st.sidebar.warning(f"Erro API ({res.status_code})")
                break
        return all_results
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return []

# --- INTERFACE ---
def executar():
    st.title("🛰️ Radar de Recursos Governamentais")
    st.caption("CORE ESSENCE - Inteligência em Dados Públicos (Via API Federal)")

    with st.sidebar:
        st.header("🔑 Painel do Consultor")
        plano = st.selectbox("Seu Plano:", ["Start", "Professional", "Enterprise"])
        st.divider()
        st.header("📍 Parâmetros de Busca")
        # Padrão: Presidente Prudente (3541406)
        ibge = st.text_input("Código IBGE do Município", value="3541406")
        ano = st.selectbox("Ano", [2026, 2025, 2024])
        mes = st.selectbox("Mês", [f"{i:02d}" for i in range(1, 13)])
        
        btn_radar = st.button("Rastrear Agora")

    if btn_radar:
        data_ref = f"{ano}{mes}"
        with st.spinner(f"Acessando base federal de {data_ref}..."):
            resultados = buscar_dados_governo(ibge, data_ref)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # Métricas Rápidas
                total = df['valor'].sum()
                st.metric("Total Identificado no Mês", f"R$ {total:,.2f}")

                # Gráfico e Tabela
                st.subheader("📊 Distribuição de Verbas")
                st.bar_chart(df.groupby('tipoTransferencia')['valor'].sum())
                
                st.subheader("📋 Relatório Detalhado")
                st.dataframe(df[['tipoTransferencia', 'favorecido', 'valor', 'origemRecurso']], use_container_width=True)
                
                st.success("Busca realizada com sucesso! Dados 100% oficiais.")
            else:
                st.warning("Nenhum repasse encontrado para este IBGE neste período.")

if __name__ == "__main__":
    executar()
