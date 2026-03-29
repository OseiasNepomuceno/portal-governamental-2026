import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# 1. Configuração da Página
st.set_page_config(page_title="CORE ESSENCE - Portal 2026", layout="wide", page_icon="💎")

# --- BLOCO DE CSS PROFISSIONAL (LIMPEZA TOTAL) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden; display: none !important;}
            footer {visibility: hidden; display: none !important;}
            header {visibility: hidden; display: none !important;}
            [data-testid="stHeader"] {display: none !important;}
            .stAppDeployButton {display:none !important;}
            div[class^="viewerBadge"] {display: none !important;}
            .block-container {padding-top: 2rem !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- FUNÇÃO PARA CONECTAR AO GOOGLE SHEETS (ESCRIÇÃO/LOGS) ---
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["ID_LICENCAS"])

# --- FUNÇÃO PARA REGISTRAR LOG DE ACESSO ---
def registrar_log(usuario, acao):
    try:
        sh = conectar_google_sheets()
        wks = sh.worksheet("LOG_ACESSOS")
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        wks.append_row([agora, usuario, acao])
    except Exception as e:
        print(f"Erro ao salvar log: {e}")

# --- FUNÇÃO PARA VERIFICAR LICENÇA (LEITURA) ---
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
                        # ADICIONE A LINHA ABAIXO AQUI:
                registrar_log(user_input, "Login realizado com sucesso")
                return True, "Sucesso"
            elif status == "expirado":
                return False, "Licença expirada."
        return False, "Usuário ou senha incorretos."
    except Exception as e:
        return False, f"Erro de conexão: {e}"

# --- CONTROLE DE SESSÃO ---
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
                registrar_log(u, "Login realizado com sucesso")
                st.rerun()
            else:
                st.error(mensagem)
    st.stop()

# --- INTERFACE PÓS-LOGIN ---
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")

# Definição Dinâmica do Menu
menu = ["📊 Radar de Recursos 2026", "📈 Radar de Emendas", "📑 Revisor de Estatuto (MROSC)"]
if st.session_state.usuario_atual == "admin":
    menu.append("💼 Painel Gestão")
menu.append("🚪 Sair")

escolha = st.sidebar.radio("Navegação:", menu)

# --- LÓGICA DE NAVEGAÇÃO ---

if escolha == "🚪 Sair":
    registrar_log(st.session_state.usuario_atual, "Logout realizado")
    st.session_state.clear()
    st.rerun()

elif escolha == "💼 Painel Gestão":
    st.title("💼 Painel Administrativo de Acessos")
    try:
        sh = conectar_google_sheets()
        # Mostra os logs
        wks_logs = sh.worksheet("LOG_ACESSOS")
        df_logs = pd.DataFrame(wks_logs.get_all_records())
        st.subheader("Histórico de Logins")
        st.dataframe(df_logs.sort_index(ascending=False), use_container_width=True)
        
        # Mostra as licenças atuais
        wks_licencas = sh.worksheet("usuario") # Nome da sua aba de usuários
        df_lic = pd.DataFrame(wks_licencas.get_all_records())
        st.subheader("Gerenciamento de Licenças")
        st.table(df_lic)
    except Exception as e:
        st.error(f"Erro ao carregar dados de gestão: {e}")

elif escolha == "📊 Radar de Recursos 2026":
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
