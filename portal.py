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

if escolha == "📊 Radar de Recursos 2026":
    try:
        import recursos2026
        recursos2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar módulo: {e}")

if escolha == "📊 Radar de Recursos 2026":
    import recursos2026
    recursos2026.executar() # Importante: você vai precisar ajustar os arquivos .py conforme abaixo

elif escolha == "📈 Radar de Emendas":
    import radar_emendas_2026
    radar_emendas_2026.executar()

elif escolha == "📑 Revisor de Estatuto (MROSC)":
    import revisor_estatuto
    revisor_estatuto.executar()

elif escolha == "🚪 Sair":
    st.info("Sessão encerrada com segurança. Até logo, Oseias!")
    st.stop()
