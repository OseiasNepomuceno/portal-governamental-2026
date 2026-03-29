import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="CORE ESSENCE - Portal 2026", layout="wide", page_icon="💎")

# --- BLOCO DE CSS (ESCONDE AS MARCAS DO STREAMLIT) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stHeader"] {display: none;}
            [data-testid="stFooter"] {display: none;}
            .stAppDeployButton {display:none;}
            .block-container {padding-top: 2rem;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- FUNÇÃO DE LICENÇA ---
def verificar_licenca(user_input, pass_input):
    try:
        sheet_id = st.secrets["ID_LICENCAS"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_licencas = pd.read_csv(url)
        df_licencas['usuario'] = df_licencas['usuario'].astype(str).str.strip()
        usuario_db = df_licencas[df_licencas['usuario'] == str(user_input).strip()]
        if not usuario_db.empty:
            senha_correta = str(usuario_db.iloc[0]['senha']).strip()
            status = str(usuario_db.iloc[0]['status']).lower().strip()
            if str(pass_input).strip() == senha_correta and status == "ativo":
                return True, "Sucesso"
        return False, "Acesso Negado ou Licença Expirada."
    except Exception as e:
        return False, f"Erro: {e}"

# --- CONTROLE DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 CORE ESSENCE - Acesso")
    with st.form("login"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            ok, msg = verificar_licenca(u, p)
            if ok:
                st.session_state.logado = True
                st.session_state.user = u
                st.rerun()
            else: st.error(msg)
    st.stop()


# ABAIXO DAQUI, CHAME SEUS MÓDULOS (import recursos2026, etc)

# --- FUNÇÃO PARA VERIFICAR ACESSO NA PLANILHA ---
def verificar_licenca(user_input, pass_input):
    try:
        sheet_id = st.secrets["ID_LICENCAS"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_licencas = pd.read_csv(url)
        
        # Limpeza de dados para evitar erros de espaço ou maiúsculas
        df_licencas['usuario'] = df_licencas['usuario'].astype(str).str.strip()
        user_input_limpo = str(user_input).strip()
        
        usuario_db = df_licencas[df_licencas['usuario'] == user_input_limpo]
        
        if not usuario_db.empty:
            senha_correta = str(usuario_db.iloc[0]['senha']).strip()
            status = str(usuario_db.iloc[0]['status']).lower().strip()
            
            if str(pass_input).strip() == senha_correta and status == "ativo":
                return True, "Sucesso"
            elif status == "expirado":
                return False, "Sua licença expirou. Entre em contato para renovar."
        
        return False, "Usuário ou senha incorretos."
    except Exception as e:
        return False, f"Erro de conexão com o servidor: {e}"

# --- INICIALIZAÇÃO DO ESTADO DE LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = None

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 CORE ESSENCE - Gestão de Acessos")
    with st.form("login_form"):
        u = st.text_input("Usuário").strip()
        p = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("Acessar Portal"):
            autorizado, mensagem = verificar_licenca(u, p)
            if autorizado:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error(mensagem)
    st.stop() 

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ LOGADO ---

# Configuração do Menu Lateral
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")

# Lista de opções básica
menu = ["📊 Radar de Recursos 2026", "📈 Radar de Emendas", "📑 Revisor de Estatuto (MROSC)"]

# Se for admin, adiciona o painel de gestão
if st.session_state.usuario_atual == "admin":
    menu.append("💼 Painel Gestão")

menu.append("🚪 Sair")

escolha = st.sidebar.radio("Navegação:", menu)

# --- LÓGICA DO BOTÃO SAIR ---
if escolha == "🚪 Sair":
    st.session_state.logado = False
    st.info("Sessão encerrada com segurança.")
    if st.button("Voltar para a tela de Login"):
        st.session_state.clear() 
        st.rerun()
    st.stop()

# --- NAVEGAÇÃO DOS MÓDULOS ---

if escolha == "📊 Radar de Recursos 2026":
    try:
        import recursos2026
        recursos2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar módulo: {e}")

elif escolha == "📈 Radar de Emendas":
    try:
        import radar_emendas_2026
        radar_emendas_2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar módulo: {e}")

elif escolha == "📑 Revisor de Estatuto (MROSC)":
    try:
        import revisor_estatuto
        revisor_estatuto.executar()
    except Exception as e:
        st.error(f"Erro ao carregar módulo: {e}")

elif escolha == "💼 Painel Gestão":
    st.title("💼 Painel Administrativo - CORE ESSENCE")
    st.write(f"Olá, {st.session_state.usuario_atual}. Aqui você pode monitorar as licenças.")
    # Exemplo: Mostrar a planilha de licenças atualizada
    try:
        sheet_id = st.secrets["ID_LICENCAS"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(url)
        st.table(df)
    except:
        st.error("Não foi possível carregar o log de licenças.")
