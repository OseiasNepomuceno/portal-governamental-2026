import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime



# --- FUNÇÃO DE BUSCA NA API DO GOVERNO ---
@st.cache_data(ttl=3600)
def buscar_dados_governo(codigo_ibge, ano, mes):
    # BUSCA EXATA: Sincronizado com o nome que você salvou no Secrets
    chave = st.secrets.get("chave-api-dados")
    
    if not chave:
        st.error("🚨 Erro: A chave 'chave-api-dados' não foi encontrada nos Secrets do Streamlit.")
        return []

    # Limpeza de segurança (remove aspas ou espaços acidentais)
    token = str(chave).strip().replace('"', '').replace("'", "")
    
    # Formato MM/AAAA (Padrão exigido pelo Portal da Transparência)
    data_formatada = f"{mes}/{ano}"
    
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/transferencias/por-municipio"
    
    # CORREÇÃO DE IDENTAÇÃO AQUI (Linha 30)
    headers = {
        "chave-api-dados": token,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://portaldatransparencia.gov.br/"
    }
    
    params = {
        "codigoIbge": codigo_ibge,
        "mesAno": data_formatada,
        "pagina": 1
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 403:
            st.error(f"🚫 Erro 403: Acesso negado pelo Governo para a data {data_formatada}.")
            st.info("Sua chave foi reconhecida, mas o servidor do governo ainda está processando a autorização.")
            return []
        else:
            st.error(f"Erro {res.status_code} na API Federal. Verifique os parâmetros.")
            return []
    except Exception as e:
        st.error(f"Falha técnica de conexão: {e}")
        return []

# --- INTERFACE PRINCIPAL ---
def exibir_radar():
    st.title("🛰️ Radar de Recursos Governamentais")
    st.caption("CORE ESSENCE - Inteligência em Dados Públicos em Tempo Real")

    # --- PARÂMETROS DE BUSCA NA ÁREA PRINCIPAL (Não na Sidebar) ---
    st.markdown("### 📍 Parâmetros de Busca")
    c1, c2, c3 = st.columns([2, 1, 1]) # Cria colunas para os filtros ficarem bonitos
    
    with c1:
        ibge = st.text_input("Código IBGE do Município", value="3541406", key="ibge_input")
    with c2:
        ano = st.selectbox("Ano", [2026, 2025, 2024], index=0, key="ano_input")
    with c3:
        mes = st.selectbox("Mês", [f"{i:02d}" for i in range(1, 13)], index=0, key="mes_input")
    
    # Botão centralizado
    btn_radar = st.button("🚀 Rastrear Recursos Agora", use_container_width=True)

    if btn_radar:
        with st.spinner(f"Consultando base federal de {mes}/{ano}..."):
            resultados = buscar_dados_governo(ibge, ano, mes)
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # Tratamento de Valores
                if 'valor' in df.columns:
                    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
                
                total = df['valor'].sum() if 'valor' in df.columns else 0
                
                st.success("✅ Dados obtidos com sucesso!")
                
                # KPIs em destaque
                k1, k2 = st.columns(2)
                valor_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                k1.metric("Total Identificado", valor_formatado)
                k2.metric("Nº de Repasses", len(df))

                st.markdown("---")
                st.subheader("📋 Detalhamento das Transferências")
                
                colunas_vistas = ['tipoTransferencia', 'favorecido', 'valor', 'origemRecurso']
                colunas_finais = [c for c in colunas_vistas if c in df.columns]
                
                st.dataframe(df[colunas_finais], use_container_width=True)
            else:
                st.info(f"Nenhum dado encontrado para {mes}/{ano}. Tente um mês anterior (ex: 12/2025).")
