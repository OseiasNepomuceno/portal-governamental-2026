import streamlit as st

# 1. Configuração da Página (Sempre a primeira linha de comando Streamlit)
st.set_page_config(page_title="CORE ESSENCE - Portal 2026", layout="wide", page_icon="💎")

# 2. Inicialização do Estado de Login (Cria a "chave" na memória)
if "logado" not in st.session_state:
    st.session_state.logado = True

# 3. Criação do Menu Lateral (Define a variável 'escolha' primeiro!)
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")
menu = ["📊 Radar de Recursos 2026", "📈 Radar de Emendas", "📑 Revisor de Estatuto (MROSC)", "🚪 Sair"]
escolha = st.sidebar.radio("Navegação:", menu)

# 4. Lógica de Segurança e Logout
if escolha == "🚪 Sair":
    st.session_state.logado = False
    st.info("Sessão encerrada com segurança. Até logo, Oseias!")
    if st.button("Novo Login"):
        st.session_state.logado = True
        st.rerun()
    st.stop() # Interrompe o código aqui para quem saiu

# 5. Trava de Segurança Geral
if not st.session_state.logado:
    st.warning("Acesso restrito. Por favor, faça login.")
    st.stop()
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
