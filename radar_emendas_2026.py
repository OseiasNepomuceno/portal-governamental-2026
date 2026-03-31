import streamlit as st
import requests
import pandas as pd

# --- FUNÇÃO DE BUSCA NA API DE EMENDAS ---
@st.cache_data(ttl=3600)
def buscar_emendas_governo(ano, pagina=1):
    # Usa a mesma chave que já configuramos no Secrets
    chave = st.secrets.get("chave-api-dados")
    
    if not chave:
        st.error("🚨 Chave 'chave-api-dados' não encontrada nos Secrets.")
        return []

    token = str(chave).strip().replace('"', '').replace("'", "")
    
    # URL que validamos no Swagger
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
    
    headers = {
        "chave-api-dados": token,
        "Accept": "application/json",
        "User-Agent": "CoreEssence-Radar/1.0"
    }
    
    params = {
        "ano": ano,
        "pagina": pagina
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 403:
            st.error("🚫 Erro 403: Acesso negado à API de Emendas.")
            return []
        else:
            st.error(f"Erro {res.status_code} na API de Emendas.")
            return []
    except Exception as e:
        st.error(f"Falha de conexão: {e}")
        return []

def executar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    st.caption("CORE ESSENCE - Monitoramento de Verbas Legislativas em Tempo Real")
    st.markdown("---")

    # --- PAINEL DE FILTROS ---
    with st.sidebar:
        st.header("📍 Filtros de Emendas")
        # No radar_emendas_2026.py, altere esta linha:
        ano_sel = st.selectbox("Ano da Emenda", [2026, 2025, 2024, 2023, 2022], index=2)
        btn_buscar = st.button("🔍 Consultar Emendas")

    if btn_buscar:
        with st.spinner(f"Rastreando emendas de {ano_sel}..."):
            dados = buscar_emendas_governo(ano_sel)
            
            if dados:
                df = pd.DataFrame(dados)
                
                # --- TRATAMENTO DE VALORES ---
                # A API retorna valores como string, convertemos para número
                colunas_valor = ['valorEmpenhado', 'valorLiquidado', 'valorPago']
                for col in colunas_valor:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce').fillna(0)

                # --- MÉTRICAS ---
                total_empenhado = df['valorEmpenhado'].sum()
                total_pago = df['valorPago'].sum()
                
                m1, m2 = st.columns(2)
                m1.metric("Total Reservado (Empenhado)", f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                m2.metric("Total na Conta (Pago)", f"R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                # --- GRÁFICO DE AUTORES ---
                st.subheader("📊 Top 10 Autores de Emendas (Volume R$)")
                if 'nomeAutor' in df.columns:
                    chart_data = df.groupby('nomeAutor')['valorEmpenhado'].sum().sort_values(ascending=False).head(10)
                    st.bar_chart(chart_data)

                # --- TABELA DETALHADA ---
                st.subheader("📋 Detalhamento das Emendas")
                # Selecionamos as colunas mais importantes para o consultor
                cols_exibir = ['numeroEmenda', 'nomeAutor', 'tipoEmenda', 'funcao', 'valorEmpenhado', 'valorPago']
                cols_existentes = [c for c in cols_exibir if c in df.columns]
                st.dataframe(df[cols_existentes], use_container_width=True)
            else:
                st.info(f"Nenhuma emenda encontrada para o ano {ano_sel} ou a chave ainda está processando.")

if __name__ == "__main__":
    executar()
