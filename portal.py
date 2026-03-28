import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CORE ESSENCE - Portal 2026", layout="wide", page_icon="💎")

# --- ESTILIZAÇÃO DO MENU LATERAL ---
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")
st.sidebar.markdown("---")

# Opções do Menu
menu = [
    "📊 Radar de Recursos 2026",
    "📈 Radar de Emendas",
    "📑 Revisor de Estatuto (MROSC)",
    "🚪 Sair"
]

escolha = st.sidebar.radio("Navegação do Consultor:", menu)

# --- LÓGICA DE NAVEGAÇÃO (CHAMANDO OS OUTROS ARQUIVOS) ---

# --- LÓGICA DE NAVEGAÇÃO SEGURA ---

if escolha == "📊 Radar de Recursos 2026":
    try:
        import recursos2026
        recursos2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar Radar de Recursos: {e}")

elif escolha == "📈 Radar de Emendas":
    try:
        import radar_emendas_2026
        radar_emendas_2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar Radar de Emendas: {e}")

elif escolha == "📑 Revisor de Estatuto (MROSC)":
    try:
        import revisor_estatuto
        revisor_estatuto.executar()
    except Exception as e:
        st.error(f"Erro ao carregar Revisor de Estatuto: {e}")

elif escolha == "🚪 Sair":
    st.info("Sessão encerrada com segurança. Até logo, Oseias!")
    st.stop()
