import streamlit as st
import pandas as pd
import gdown
import os
import gspread
import smtplib
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. IMPORTAÇÃO DOS MÓDULOS ---
import radar_emendas_2026
import recursos2026
import revisor_estatuto

# --- 2. FUNÇÕES DE APOIO ---

def exibir_dashboard_boas_vindas(nome, plano, uso_revisor):
    st.markdown(f"### 👋 Bem-vindo, {nome.capitalize()}!")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; min-height: 150px;"><h4 style="margin: 0; color: #007bff;">📊 Radar 2026</h4><p style="font-size: 14px; color: #555; margin-top: 10px;">Acompanhamento estratégico de emendas.</p><span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px;">ATIVO</span></div>', unsafe_allow_html=True)

    limite_revisoes = 15 if plano == "PREMIUM" else 10
    with col2:
        st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; min-height: 150px;"><h4 style="margin: 0; color: #28a745;">📑 Revisor IA</h4><p style="font-size: 14px; color: #555; margin-top: 10px;">Análise de conformidade via IA.</p><small>Uso: <b>{uso_revisor}/{limite_revisoes}</b></small></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; min-height: 150px;"><h4 style="margin: 0; color: #856404;">🏆 Plano {plano}</h4><p style="font-size: 14px; color: #555; margin-top: 10px;">Licença ativa por 30 dias.</p></div>', unsafe_allow_html=True)
    st.divider()

def registrar_log_acesso(usuario, plano):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
        client = gspread.authorize(creds)
        planilha = client.open("ID_LICENÇAS").worksheet("logs")
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        # Registra: Data, Usuário, Plano
        planilha.append_row([data_hora, usuario, plano])
    except Exception as e:
        print(f"Erro log: {e}")

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
                info = dados.to_dict()
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = u_clean
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BÁSICO')).upper()
                st.session_state['usuario_logado'] = {
                    'LOCALIDADE': dados.iloc[4] if len(dados) >= 5 else "BR",
                    'REVISOES_USADAS': dados.iloc[5] if len(dados) >= 6 else 0
                }
                # CHAMADA DO REGISTRO DE LOG
                registrar_log_acesso(u_clean, st.session_state['usuario_plano'])
                return True
        return False
    except Exception as e:
        st.error(f"Erro autenticação: {e}")
        return False

# --- CONFIGURAÇÃO PÁGINA ---
st.set_page_config(page_title="Core Essence", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.title("🛰️ Core Essence")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("FAZER LOGIN", use_container_width=True, type="primary"):
                    st.session_state['tela'] = 'login'; st.rerun()
        
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Login")
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p): st.rerun()
                    else: st.error("Acesso negado.")
            if st.button("Voltar"): st.session_state['tela'] = 'home'; st.rerun()

    else:
        with st.sidebar:
            st.title("Core Essence")
            user = st.session_state['usuario_nome']
            plano = st.session_state['usuario_plano']
            st.info(f"👤 {user.upper()}")
            st.success(f"🏆 {plano}")
            st.divider()
            
            menu = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            if user == "admin":
                menu.append("🔧 Gestão Admin")
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        if escolha == "🚪 Sair":
            st.session_state.clear(); st.rerun()
        elif escolha == "🔧 Gestão Admin":
            st.title("🔧 Gestão Administrativa")
            try:
                nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
                creds = Credentials.from_service_account_file(nome_da_chave, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
                client = gspread.authorize(creds)
                sh = client.open("ID_LICENÇAS")
                
                st.subheader("📝 Logs de Acesso")
                logs = pd.DataFrame(sh.worksheet("logs").get_all_records())
                st.dataframe(logs, use_container_width=True)
                
                st.subheader("👥 Usuários")
                users = pd.DataFrame(sh.worksheet("usuario").get_all_records())
                st.dataframe(users, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
        elif escolha == "🏛️ Radar de Emendas": radar_emendas_2026.exibir_radar()
        elif escolha == "📊 Recursos 2026": recursos2026.exibir_recursos()
        elif escolha == "📜 Revisor de Estatuto": revisor_estatuto.exibir_revisor()
        else:
            exibir_dashboard_boas_vindas(user, plano, st.session_state['usuario_logado']['REVISOES_USADAS'])

if __name__ == "__main__":
    executar()
