import streamlit as st
import pandas as pd
import gdown
import os
import importlib
import gspread
from google.oauth2.service_account import Credentials

# --- FUNÇÕES DE APOIO ---
def salvar_cadastro_google_sheets(dados_cliente):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
        client = gspread.authorize(creds)
        planilha = client.open("ID_LICENÇAS").worksheet("usuario")
        planilha.append_row(dados_cliente)
        return True
    except Exception as e:
        st.error(f"Erro técnico ao acessar a planilha: {e}")
        return False

def autenticar_usuario(usuario_digitado, senha_digitada):
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_login.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        gdown.download(url, nome_arquivo, quiet=True)
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        df['usuario'] = df['usuario'].astype(str).str.strip()
        df['senha'] = df['senha'].astype(str).str.strip()
        user_row = df[(df['usuario'] == str(usuario_digitado).strip()) & 
                      (df['senha'] == str(senha_digitada).strip())]
        if not user_row.empty:
            dados = user_row.iloc[0]
            status_bruto = dados.get('STATUS', dados.get('status', 'ativo'))
            if str(status_bruto).lower().strip() == 'ativo':
                st.session_state['usuario_logado'] = dados.to_dict() 
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = dados.get('usuario', 'Consultor')
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BRONZE')).upper().strip()
                return True
        return False
    except: return False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Core Essence", page_icon="🛰️", layout="wide")

# --- NAVEGAÇÃO ---
def executar():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.title("🛰️ Core Essence - Inteligência Governamental")
            c1, c2 = st.columns(2)
            if c1.button("👤 LOGIN", use_container_width=True):
                st.session_state['tela'] = 'login'
                st.rerun()
            if c2.button("🚀 CADASTRO", use_container_width=True):
                st.session_state['tela'] = 'cadastro'
                st.rerun()
        
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Acesso ao Portal")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p):
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")

    else:
        # --- PORTAL APÓS LOGIN ---
        with st.sidebar:
            st.title("Core Essence")
            plano = st.session_state.get('usuario_plano', 'BRONZE')
            user_raw = st.session_state.get('usuario_nome', 'Consultor')
            user_comparar = str(user_raw).lower().strip()
            
            st.info(f"🏆 Plano: {plano}")

            menu = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão de Estatuto"]
            
            # TRAVA DE ADMIN
            if user_comparar == "admin":
                menu.append("⚙️ Gestão Administrativa")
            
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        if escolha == "📊 Recursos":
            import recursos2026 as rec
            importlib.reload(rec)
            rec.exibir_radar()
        elif escolha == "🏛️ Radar de Emendas":
            import radar_emenda_2026 as radar
            importlib.reload(radar)
            radar.exibir_radar()
        elif escolha == "⚙️ Gestão Administrativa":
            import gestao as adm
            importlib.reload(adm)
            adm.exibir_gestao()
        elif escolha == "🚪 Sair":
            st.session_state.clear()
            st.rerun()

# --- DISPARO DO APP ---
if __name__ == "__main__":
    executar()
