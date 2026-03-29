import streamlit as st

# 1. Configuração da Página
st.set_page_config(page_title="CORE ESSENCE - Portal 2026", layout="wide", page_icon="💎")

# --- SISTEMA DE AUTENTICAÇÃO ---
# Inicializa o estado de login como falso se for o primeiro acesso
if "logado" not in st.session_state:
    st.session_state.logado = False

def tela_de_login():
    st.title("🔐 Acesso Restrito - CORE ESSENCE")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        botao_entrar = st.form_submit_button("Entrar no Portal")
        
        if botao_entrar:
            # VOCÊ PODE MUDAR A SENHA AQUI:
            if usuario == "oseias" and senha == "core2026":
                st.session_state.logado = True
                st.success("Acesso autorizado! Carregando...")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# --- LÓGICA DE BLOQUEIO ---
if not st.session_state.logado:
    tela_de_login()
    st.stop() # Interrompe tudo e só mostra a tela de login

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ LOGADO ---
# Menu Lateral
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")
menu = ["📊 Radar de Recursos 2026", "📈 Radar de Emendas", "📑 Revisor de Estatuto (MROSC)", "🚪 Sair"]
escolha = st.sidebar.radio("Navegação:", menu)

# Lógica do Botão Sair
if escolha == "🚪 Sair":
    st.session_state.logado = False
    st.info("Sessão encerrada com segurança.")
    if st.button("Voltar para a tela de Login"):
        st.rerun()
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
