import streamlit as st
import pandas as pd
import gdown
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

# --- 1. CONFIGURAÇÕES DE LINKS ---
URL_CLIENTES_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4dCgWCWMhrPNgrSMkXDd2s2FA9eP_gSu9pL8c1MfuJk3YvcQw0kVMq6i8p_FA2Zz7IhAYEexg3CoI/pub?gid=1923834729&single=true&output=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzH2C-ski7ARq9XC6YweSMKf1VpSuxGvJHjAKSyL85ILsjLxGg6hDTxUHxLk40iEW7HTg/exec"

# --- 2. IMPORTAÇÃO DOS MÓDULOS ---
import radar_emendas_2026
import recursos2026
import revisor_estatuto

# --- 3. FUNÇÕES DE APOIO ---

def obter_creds():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
    if os.path.exists(nome_da_chave):
        return Credentials.from_service_account_file(nome_da_chave, scopes=scope)
    return None

def autenticar_usuario(usuario_digitado, senha_digitada):
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_login.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if os.path.exists(nome_arquivo): os.remove(nome_arquivo)
        gdown.download(url, nome_arquivo, quiet=True)
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        u_clean = str(usuario_digitado).strip().lower()
        p_clean = str(senha_digitada).strip()

        user_row = df[(df['USUARIO'].astype(str).str.strip().str.lower() == u_clean) & 
                      (df['SENHA'].astype(str).str.strip() == p_clean)]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS', 'pendente')).lower().strip() == 'ativo':
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = u_clean
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BÁSICO')).upper()
                return True
        return False
    except: return False

# --- 4. MÓDULO GESTÃO DE CLIENTES ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    user_ref = st.session_state.get('usuario_nome', '').lower()

    try:
        # Lendo o CSV com cache para performance
        df = pd.read_csv(URL_CLIENTES_CSV)
        meus_clientes = df[df['Consultor'].astype(str).str.lower() == user_ref]
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        meus_clientes = pd.DataFrame()

    t1, t2, t3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Relatórios"])

    with t1:
        if meus_clientes.empty:
            st.info("Você ainda não possui clientes vinculados ao seu usuário.")
        else:
            st.dataframe(meus_clientes, use_container_width=True, hide_index=True)

    with t2:
        with st.form("add_client", clear_on_submit=True):
            st.subheader("Cadastrar Novo Cliente")
            c_cnpj = st.text_input("CNPJ")
            c_nome = st.text_input("Nome do Cliente / Ente")
            c_tel = st.text_input("Telefone")
            if st.form_submit_button("Salvar na Planilha"):
                if c_cnpj and c_nome:
                    payload = {
                        "acao": "incluir", 
                        "consultor": user_ref, 
                        "cnpj": c_cnpj, 
                        "nome": c_nome,
                        "telefone": c_tel
                    }
                    try:
                        requests.post(WEBHOOK_URL, json=payload)
                        st.success(f"Cliente {c_nome} enviado com sucesso!")
                        st.balloons()
                    except:
                        st.error("Erro ao conectar com o servidor.")
                else:
                    st.warning("Preencha CNPJ e Nome.")

# --- 5. INTERFACE PRINCIPAL ---

st.set_page_config(page_title="CoreGov2", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        # TELA DE LOGIN (Simplificada para este exemplo)
        st.title("🔑 Acesso ao Portal CoreGov")
        with st.form("login"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if autenticar_usuario(u, p): st.rerun()
                else: st.error("Usuário ou senha incorretos.")
    else:
        # --- SIDEBAR AJUSTADA ---
        with st.sidebar:
            if os.path.exists("logocoregov.png"):
                st.image("logocoregov.png", use_container_width=True)
            
            st.title("CoreGov")
            user = st.session_state.get('usuario_nome', 'admin')
            st.info(f"👤 CONSULTOR: {user.upper()}")
            
            st.subheader("Navegação")
            opcoes_menu = [
                "🏠 Home", 
                "📊 Recursos 2026", 
                "🏛️ Radar de Emendas", 
                "📜 Revisor de Estatuto", 
                "💼 Clientes Atendidos" # <--- OPÇÃO INSERIDA AQUI
            ]
            
            if user.lower() == "admin":
                opcoes_menu.append("🔧 Gestão Admin")
            
            escolha = st.radio("Selecione o Módulo:", opcoes_menu)
            
            st.divider()
            if st.button("🚪 Sair do Sistema", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        # --- LÓGICA DE EXIBIÇÃO DE TELAS ---
        if escolha == "🏠 Home":
            st.markdown(f"### 👋 Bem-vindo ao Painel de Controle, {user.capitalize()}!")
            st.info("Utilize o menu lateral para acessar as ferramentas de inteligência ou gerenciar sua carteira de clientes.")
            
        elif escolha == "💼 Clientes Atendidos":
            gerenciar_clientes()
            
        elif escolha == "🏛️ Radar de Emendas":
            radar_emendas_2026.exibir_radar()
            
        elif escolha == "📊 Recursos 2026":
            recursos2026.exibir_recursos()
            
        elif escolha == "📜 Revisor de Estatuto":
            revisor_estatuto.exibir_revisor()
            
        elif escolha == "🔧 Gestão Admin":
            st.title("🔧 Painel Administrativo")
            st.write("Acesso restrito para monitoramento global.")

if __name__ == "__main__":
    executar()
