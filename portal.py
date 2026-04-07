import streamlit as st
import pandas as pd
import gdown
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests # Necessário para o Webhook de Clientes

# --- 1. IMPORTAÇÃO DOS MÓDULOS ---
import radar_emendas_2026
import recursos2026
import revisor_estatuto

# --- 2. FUNÇÕES DE APOIO ---

def obter_creds():
    """Gerencia a autenticação usando Secrets (Nuvem) ou Arquivo JSON (Local)"""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    
    nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
    if os.path.exists(nome_da_chave):
        return Credentials.from_service_account_file(nome_da_chave, scopes=scope)
    
    return None

def registrar_log_acesso(usuario, plano):
    try:
        creds = obter_creds()
        if creds:
            client = gspread.authorize(creds)
            sh = client.open("ID_LICENÇAS")
            planilha = sh.worksheet("LOG_ACESSOS")
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            acao = f"Login Efetuado - Plano {plano}"
            planilha.append_row([data_hora, usuario, acao])
    except Exception as e:
        st.error(f"Erro ao registrar log: {e}")

def salvar_cadastro_google_sheets(dados_cliente):
    try:
        creds = obter_creds()
        if creds:
            client = gspread.authorize(creds)
            planilha = client.open("ID_LICENÇAS").worksheet("usuario")
            planilha.append_row(dados_cliente)
            return True
    except: return False

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
                st.session_state['usuario_logado'] = {
                    'LOCALIDADE': dados.iloc[4] if len(dados) >= 5 else "BR",
                    'REVISOES_USADAS': dados.iloc[5] if len(dados) >= 6 else 0
                }
                registrar_log_acesso(u_clean, st.session_state['usuario_plano'])
                return True
        return False
    except: return False

# --- 3. MÓDULO DE GESTÃO DE CLIENTES ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    st.info(f"Consultor Responsável: {st.session_state.get('usuario_nome', '').upper()}")
    
    # Espaço para a lógica de Incluir, Alterar e Excluir que integra com a aba "Clientes"
    aba1, aba2, aba3 = st.tabs(["👥 Clientes", "➕ Novo Cadastro", "📊 Relatórios de Prospecção"])
    
    with aba1:
        st.write("Lista de clientes carregada da Planilha ID_LICENÇAS...")
        # Aqui entrará o st.dataframe filtrado
    
    with aba2:
        with st.form("novo_cliente_gov"):
            st.text_input("CNPJ")
            st.text_input("Nome do Cliente")
            st.text_input("Telefone")
            st.form_submit_button("Salvar na Nuvem")

# --- 4. COMPONENTES DE INTERFACE ---

def exibir_home_publica():
    if os.path.exists("logocoregov.png"):
        col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
        with col_l2:
            st.image("logocoregov.png", use_container_width=True)
    
    st.markdown("<h1 style='text-align: center; color: #007bff;'>🛰️ CoreGov</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #007bff; min-height: 200px; text-align: center;"><h4>👤 Área do Cliente</h4><p>Acesse com seu CNPJ para acompanhar seus relatórios.</p></div>', unsafe_allow_html=True)
        if st.button("ACOMPANHAMENTO (CNPJ)", use_container_width=True):
             st.session_state['tela'] = 'area_cliente'
             st.rerun()

    with col2:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #28a745; min-height: 200px; text-align: center;"><h4>🚀 Seja Consultor</h4><p>Cadastre-se para gerenciar sua carteira e usar IA.</p></div>', unsafe_allow_html=True)
        if st.button("LOGIN CONSULTOR", key="btn_login_home", use_container_width=True, type="primary"):
            st.session_state['tela'] = 'login'
            st.rerun()

    with col3:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #ffc107; min-height: 200px; text-align: center;"><h4>🛰️ Ecossistema</h4><p>Tecnologia para captação de recursos.</p></div>', unsafe_allow_html=True)
        if st.button("CRIAR CONTA", use_container_width=True):
            st.session_state['tela'] = 'cadastro'
            st.rerun()

def exibir_dashboard_boas_vindas(nome, plano, uso_revisor):
    st.markdown(f"### 👋 Bem-vindo ao CoreGov, {nome.capitalize()}!")
    col1, col2, col3 = st.columns(3)
    with col1: st.success("📊 Radar 2026 Ativo")
    with col2: st.info(f"📑 Revisor IA: {uso_revisor} usos")
    with col3: st.warning(f"🏆 Plano {plano}")
    st.divider()

# --- 5. EXECUÇÃO PRINCIPAL ---

st.set_page_config(page_title="CoreGov - Inteligência Governamental", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home': exibir_home_publica()
        elif st.session_state['tela'] == 'cadastro': tela_cadastro()
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Login Consultor")
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p): st.rerun()
                    else: st.error("Acesso negado.")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
        elif st.session_state['tela'] == 'area_cliente':
            st.title("🔑 Área de Acompanhamento (Cliente)")
            cnpj_input = st.text_input("Digite o CNPJ da sua Entidade:")
            if st.button("Acessar Relatório"):
                st.info("Buscando dados na planilha...")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
    else:
        with st.sidebar:
            if os.path.exists("logocoregov.png"):
                st.image("logocoregov.png", use_container_width=True)
            
            st.title("CoreGov")
            user = st.session_state.get('usuario_nome', 'admin')
            st.info(f"👤 CONSULTOR: {user.upper()}")
            
            # --- MENU ESTRUTURADO ---
            st.subheader("🛰️ Inteligência de Dados")
            menu_radar = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            escolha_radar = st.radio("Módulos de Consulta:", menu_radar)
            
            st.divider()
            
            st.subheader("💼 Gestão Consultiva")
            menu_gestao = ["Clientes Atendidos"]
            if user.lower() == "admin": menu_gestao.append("🔧 Gestão Admin")
            escolha_gestao = st.selectbox("Ações de Consultor:", ["Navegar..."] + menu_gestao)
            
            st.divider()
            if st.button("🚪 Sair do Sistema", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        # --- LÓGICA DE EXIBIÇÃO ---
        if escolha_gestao == "Clientes Atendidos":
            gerenciar_clientes()
        elif escolha_gestao == "🔧 Gestão Admin":
            # (Mantém sua lógica de Admin original...)
            st.title("🔧 Gestão Administrativa CoreGov")
        elif escolha_radar == "🏛️ Radar de Emendas": radar_emendas_2026.exibir_radar()
        elif escolha_radar == "📊 Recursos 2026": recursos2026.exibir_recursos()
        elif escolha_radar == "📜 Revisor de Estatuto": revisor_estatuto.exibir_revisor()
        else:
            exibir_dashboard_boas_vindas(user, st.session_state.get('usuario_plano', 'BÁSICO'), st.session_state.get('usuario_logado', {}).get('REVISOES_USADAS', 0))

if __name__ == "__main
