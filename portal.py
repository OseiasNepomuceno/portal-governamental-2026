import streamlit as st

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Plataforma Governamental 2026", layout="wide", page_icon="🏛️")


# --- SISTEMA DE LOGIN ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown("<h1 style='text-align: center;'>🔐 Área do Consultor</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Usuário (E-mail)")
        password = st.text_input("Senha", type="password")
        if st.button("Acessar Sistema"):
            # --- CADASTRO DE CLIENTES (Altere aqui para novos usuários) ---
            if user == "cliente@teste.com" and password == "2026_sucesso":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Credenciais inválidas.")
    return False


# --- CONTEÚDO PROTEGIDO ---
if check_password():
    # MENU LATERAL PADRONIZADO
    st.sidebar.markdown("# 🚀 Menu de Consultoria")
    st.sidebar.markdown("---")

    pagina = st.sidebar.radio(
        "Selecione o Módulo:",
        [
            "🏠 Início",
            "🔍 Radar de Recursos",  # Nome Padronizado
            "🏛️ Radar de Emendas",  # Nome Padronizado
            "⚖️ Revisor de Estatuto"  # Nome Padronizado
        ]
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("Sair (Logout)"):
        st.session_state["password_correct"] = False
        st.rerun()

    # --- NAVEGAÇÃO ENTRE OS MÓDULOS ---
    if pagina == "🏠 Início":
        st.title("🏛️ Plataforma de Inteligência Governamental")
        st.markdown("### Bem-vindo, Consultor.")
        st.info("Utilize o menu lateral para acessar as ferramentas de análise de 2026.")

        st.markdown("""
        **Módulos Ativos:**
        * **Radar de Recursos:** Monitoramento de convênios federais (Transferegov).
        * **Radar de Emendas:** Rastreamento de verbas por parlamentar e partido.
        * **Revisor de Estatuto:** Inteligência Artificial para adequação jurídica.
        """)

    elif pagina == "🔍 Radar de Recursos":
        try:
            with open("recursos2026.py", encoding="utf-8") as f:
                exec(f.read())
        except Exception as e:
            st.error(f"Erro ao carregar o módulo: {e}")

    elif pagina == "🏛️ Radar de Emendas":
        try:
            with open("radar_emendas_2026.py", encoding="utf-8") as f:
                exec(f.read())
        except Exception as e:
            st.error(f"Erro ao carregar o módulo: {e}")

    elif pagina == "⚖️ Revisor de Estatuto":
        try:
            with open("revisor_estatuto_hibrido.py", encoding="utf-8") as f:
                exec(f.read())
        except Exception as e:
            st.error(f"Erro ao carregar o módulo: {e}")