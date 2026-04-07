import streamlit as st
import pandas as pd
import gdown
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

# --- 1. CONFIGURAÇÕES DE LINKS ---
# COLE SEU LINK CSV ABAIXO:
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
        
        # AJUSTE 2: NORMALIZAÇÃO PARA MINÚSCULO (Case-Insensitive)
        u_clean = str(usuario_digitado).strip().lower()
        p_clean = str(senha_digitada).strip()

        user_row = df[(df['USUARIO'].astype(str).str.strip().str.lower() == u_clean) & 
                      (df['SENHA'].astype(str).str.strip() == p_clean)]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS', 'pendente')).lower().strip() == 'ativo':
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = u_clean # Salva sempre em minúsculo
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BÁSICO')).upper()
                st.session_state['usuario_logado'] = {
                    'LOCALIDADE': dados.iloc[4] if len(dados) >= 5 else "BR",
                    'REVISOES_USADAS': dados.iloc[5] if len(dados) >= 6 else 0
                }
                return True
        return False
    except: return False

# --- 4. MÓDULO GESTÃO DE CLIENTES ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    user_ref = st.session_state.get('usuario_nome', '').lower()

    try:
        df = pd.read_csv(URL_CLIENTES_CSV)
        # Filtro de segurança: Consultor só vê o dele
        meus_clientes = df[df['Consultor'].astype(str).str.lower() == user_ref]
    except:
        meus_clientes = pd.DataFrame()

    t1, t2, t3 = st.tabs(["👥 Carteira", "➕ Novo Cadastro", "📊 Relatórios"])

    with t1:
        if meus_clientes.empty:
            st.info("Nenhum cliente cadastrado para o seu usuário.")
        else:
            st.dataframe(meus_clientes, use_container_width=True, hide_index=True)

    with t2:
        with st.form("add_client"):
            c_cnpj = st.text_input("CNPJ")
            c_nome = st.text_input("Nome Cliente")
            if st.form_submit_button("Salvar Cliente"):
                payload = {"acao": "incluir", "consultor": user_ref, "cnpj": c_cnpj, "nome": c_nome}
                requests.post(WEBHOOK_URL, json=payload)
                st.success("Enviado para a planilha!")

# --- 5. INTERFACE ---

st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        # Lógica de Login/Home (Mantida conforme seu código original)
        pass 
    else:
        with st.sidebar:
            st.title("🛰️ CoreGov")
            user = st.session_state.get('usuario_nome', 'admin')
            st.info(f"👤 {user.upper()}")
            
            # AJUSTE 3: ESTRUTURA DE NAVEGAÇÃO ÚNICA
            st.subheader("Menu Principal")
            opcoes_menu = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Clientes Atendidos"]
            
            if user.lower() == "admin":
                opcoes_menu.append("🔧 Gestão Admin")
            
            escolha = st.radio("Selecione o Módulo:", opcoes_menu)
            
            st.divider()
            if st.button("🚪 Sair"):
                st.session_state.clear()
                st.rerun()

        # --- LÓGICA DE EXIBIÇÃO DE TELAS ---
        if escolha == "🏠 Home":
            st.markdown(f"### 👋 Bem-vindo, {user.capitalize()}!")
            st.write("Selecione um módulo no menu lateral para começar.")
            
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
            # Sua lógica de admin...

if __name__ == "__main__":
    executar()
