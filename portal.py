import streamlit as st
import pandas as pd
import gdown
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

# --- 1. CONFIGURAÇÕES DE LINKS E APIs ---
# Substitua pelo link que você copiou do Google Sheets (Publicar na Web -> CSV)
URL_CLIENTES_CSV = "COLE_AQUI_O_LINK_QUE_VOCE_COPIOU"
# URL do seu Webhook (Google Apps Script) para Salvar/Alterar
WEBHOOK_URL = st.secrets.get("url_webhook_gestao", "SUA_URL_DO_APPS_SCRIPT_AQUI")

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
    except: pass

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

# --- 4. MÓDULO DE GESTÃO DE CLIENTES (CRUD) ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    consultor_atual = st.session_state.get('usuario_nome', '').lower()

    # Leitura dos dados via CSV Público
    try:
        df_clientes = pd.read_csv(URL_CLIENTES_CSV)
        # Filtra apenas os clientes deste consultor
        meus_clientes = df_clientes[df_clientes['Consultor'].astype(str).str.lower() == consultor_atual]
    except:
        st.error("Não foi possível carregar a base de clientes. Verifique o link CSV.")
        meus_clientes = pd.DataFrame()

    aba1, aba2, aba3 = st.tabs(["👥 Meus Clientes", "➕ Novo Cadastro", "📊 Serviços e Relatórios"])

    with aba1:
        if meus_clientes.empty:
            st.info("Você ainda não possui clientes cadastrados na sua carteira.")
        else:
            st.dataframe(meus_clientes, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("⚙️ Ações Rápidas")
            cliente_alvo = st.selectbox("Selecione um cliente para Gerenciar:", meus_clientes['Nome Cliente'].tolist())
            
            col_ed, col_ex = st.columns(2)
            if col_ed.button("📝 Editar Dados", use_container_width=True):
                st.info("Funcionalidade de edição em desenvolvimento...")
            if col_ex.button("🗑️ Excluir Cliente", use_container_width=True, type="secondary"):
                st.warning(f"Deseja realmente remover {cliente_alvo} da sua base?")

    with aba2:
        with st.form("cadastro_cliente_gov", clear_on_submit=True):
            st.subheader("Dados da Entidade/Cliente")
            f_cnpj = st.text_input("CNPJ")
            f_nome = st.text_input("Nome do Cliente / Prefeitura")
            f_end = st.text_input("Endereço")
            col_a, col_b = st.columns(2)
            f_tel = col_a.text_input("Telefone de Contato")
            f_mail = col_b.text_input("E-mail Principal")
            
            if st.form_submit_button("🚀 CADASTRAR CLIENTE"):
                if f_cnpj and f_nome:
                    payload = {
                        "acao": "incluir",
                        "consultor": consultor_atual,
                        "cnpj": f_cnpj,
                        "nome": f_nome,
                        "endereco": f_end,
                        "telefone": f_tel,
                        "email": f_mail
                    }
                    try:
                        r = requests.post(WEBHOOK_URL, json=payload)
                        st.success(f"✅ {f_nome} adicionado com sucesso!")
                        st.balloons()
                    except:
                        st.error("Erro ao conectar com o servidor. Tente novamente.")
                else:
                    st.warning("CNPJ e Nome são obrigatórios.")

    with aba3:
        st.subheader("📝 Relatório de Prospecção")
        if not meus_clientes.empty:
            sel_rel = st.selectbox("Selecione o Cliente para o Relatório:", meus_clientes['Nome Cliente'].tolist())
            servicos = st.multiselect("Serviços em Andamento:", ["Radar de Emendas", "Captação Transferegov", "Revisão de Estatuto", "Prospecção Ativa"])
            notas = st.text_area("Notas da Consultoria (O cliente visualizará este campo)")
            if st.button("Atualizar Relatório"):
                st.success("Relatório salvo e disponível para o cliente!")
        else:
            st.info("Cadastre um cliente primeiro para gerar relatórios.")

# --- 5. COMPONENTES DE INTERFACE ---

def exibir_home_publica():
    if os.path.exists("logocoregov.png"):
        col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
        with col_l2: st.image("logocoregov.png", use_container_width=True)
    
    st.markdown("<h1 style='text-align: center; color: #007bff;'>🛰️ CoreGov</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #007bff; min-height: 200px; text-align: center;"><h4>👤 Área do Cliente</h4><p>Acompanhamento de relatórios via CNPJ.</p></div>', unsafe_allow_html=True)
        if st.button("ACOMPANHAMENTO (CNPJ)", use_container_width=True):
             st.session_state['tela'] = 'area_cliente'
             st.rerun()
    with col2:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #28a745; min-height: 200px; text-align: center;"><h4>🚀 Seja Consultor</h4><p>Acesse o painel de inteligência CoreGov.</p></div>', unsafe_allow_html=True)
        if st.button("LOGIN CONSULTOR", key="btn_login_home", use_container_width=True, type="primary"):
            st.session_state['tela'] = 'login'
            st.rerun()
    with col3:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #ffc107; min-height: 200px; text-align: center;"><h4>🛰️ Ecossistema</h4><p>Tecnologia para captação estratégica.</p></div>', unsafe_allow_html=True)
        if st.button("CRIAR CONTA", use_container_width=True):
            st.session_state['tela'] = 'cadastro'
            st.rerun()

# --- 6. EXECUÇÃO PRINCIPAL ---

st.set_page_config(page_title="CoreGov - Inteligência Governamental", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home': exibir_home_publica()
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
            st.title("🔑 Área do Cliente (Acompanhamento)")
            cnpj_login = st.text_input("Digite o CNPJ da Entidade:")
            if st.button("Ver Relatório de Progresso"):
                st.info(f"Buscando status para o CNPJ: {cnpj_login}...")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
    else:
        with st.sidebar:
            if os.path.exists("logocoregov.png"): st.image("logocoregov.png", use_container_width=True)
            st.title("CoreGov")
            user = st.session_state.get('usuario_nome', 'admin')
            st.info(f"👤 CONSULTOR: {user.upper()}")
            
            st.subheader("🛰️ Inteligência")
            menu_radar = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            escolha_radar = st.radio("Selecione:", menu_radar)
            
            st.divider()
            st.subheader("💼 Consultoria")
            menu_gestao = ["Clientes Atendidos"]
            if user.lower() == "admin": menu_gestao.append("🔧 Gestão Admin")
            escolha_gestao = st.selectbox("Gerenciamento:", ["Navegar..."] + menu_gestao)
            
            st.divider()
            if st.button("🚪 Sair", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        # Lógica de Telas
        if escolha_gestao == "Clientes Atendidos":
            gerenciar_clientes()
        elif escolha_radar == "🏛️ Radar de Emendas": radar_emendas_2026.exibir_radar()
        elif escolha_radar == "📊 Recursos 2026": recursos2026.exibir_recursos()
        elif escolha_radar == "📜 Revisor de Estatuto": revisor_estatuto.exibir_revisor()
        else:
            st.markdown(f"### 👋 Bem-vindo ao CoreGov, {user.capitalize()}!")
            st.write("Utilize o menu lateral para acessar as ferramentas de dados ou gerenciar seus clientes.")

if __name__ == "__main__":
    executar()
