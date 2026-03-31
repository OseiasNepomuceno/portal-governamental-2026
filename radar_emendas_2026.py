import streamlit as st
import requests
import pandas as pd

# --- FUNÇÃO DE BUSCA NA API DE EMENDAS ---
@st.cache_data(ttl=3600)
def buscar_emendas_governo(ano, pagina=1):
    chave = st.secrets.get("chave-api-dados")
    
    if not chave:
        st.error("🚨 Chave 'chave-api-dados' não encontrada nos Secrets.")
        return []

    token = str(chave).strip().replace('"', '').replace("'", "")
    url = "https://api.portaldatransparencia.gov.br/api-de-dados/emendas"
    
    headers = {
        "chave-api-dados": token,
        "Accept": "application/json",
        "User-Agent": "CoreEssence-Radar/1.0"
    }
    
    params = {"ano": ano, "pagina": pagina}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

def executar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    st.caption("CORE ESSENCE - Monitoramento de Verbas Legislativas em Tempo Real")
    st.markdown("---")

    with st.sidebar:
        st.header("📍 Filtros de Emendas")
        ano_sel = st.selectbox("Ano da Emenda", [2026, 2025, 2024, 2023], index=2)
        btn_buscar = st.button("🔍 Consultar Emendas")

    if btn_buscar:
        with st.spinner(f"Rastreando emendas de {ano_sel}..."):
            dados = buscar_emendas_governo(ano_sel)
            
            if dados:
                df = pd.DataFrame(dados)
                
                # --- TRATAMENTO DE VALORES (CORRIGIDO PARA SAIR DO R$ 0,00) ---
                colunas_valor = ['valorEmpenhado', 'valorLiquidado', 'valorPago']
                for col in colunas_valor:
                    if col in df.columns:
                        # Limpeza profunda: remove pontos e troca vírgula por ponto
                        df[col] = df[col].astype(str).str.replace('.', '', regex=False)
                        df[col] = df[col].str.replace(',', '.', regex=False)
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                # --- MÉTRICAS ---
                total_empenhado = df['valorEmpenhado'].sum()
                total_pago = df['valorPago'].sum()
                
                m1, m2 = st.columns(2)
                # Formatação Brasileira
                v_emp = f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                v_pag = f"R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                m1.metric("Total Reservado (Empenhado)", v_emp)
                m2.metric("Total na Conta (Pago)", v_pag)

                # --- GRÁFICO ---
                st.subheader("📊 Volume por Autor (Top 10)")
                if 'nomeAutor' in df.columns:
                    # Agrupa pelo nome do autor e soma os valores reais
                    chart_data = df.groupby('nomeAutor')['valorEmpenhado'].sum().sort_values(ascending=False).head(10)
                    st.bar_chart(chart_data)

                # --- TABELA ---
                st.subheader("📋 Detalhamento")
                cols_exibir = ['numeroEmenda', 'nomeAutor', 'tipoEmenda', 'funcao', 'valorEmpenhado', 'valorPago']
                cols_finais = [c for c in cols_exibir if c in df.columns]
                st.dataframe(df[cols_finais], use_container_width=True)
            else:
                st.info("Nenhum dado retornado para este ano.")

if __name__ == "__main__":
    executar()
