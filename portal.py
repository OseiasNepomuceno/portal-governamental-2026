import streamlit as st
import pandas as pd
import gdown
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. IMPORTAÇÃO DOS MÓDULOS ---
import radar_emendas_2026
import recursos2026
import revisor_estatuto

# --- 2. FUNÇÕES DE APOIO ---

def registrar_log_acesso(usuario, plano):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        if os.path.exists(nome_da_chave):
            creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
            client = gspread.authorize(creds)
            sh = client.open("ID_LICENÇAS")
            planilha = sh.worksheet("logs")
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            planilha.append_row([data_hora, usuario, plano])
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def salvar_cadastro_google_sheets(dados_cliente):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
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

# --- 3. COMPONENTES DE INTERFACE ---

def exibir_home_publica():
    st.markdown("<h1 style='text-align: center; color: #007bff;'>🛰️ CoreGov</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
    st.write("\n")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #007bff; min-height: 200px; text-align: center;"><h4>👤 Já é Cliente?</h4><p>Acesse sua área exclusiva para monitorar emendas e recursos.</p></div>', unsafe_allow_html=True)
        if st.button("FAZER LOGIN", key="btn_login_home", use_container_width=True, type="primary"):
            st.session_state['tela'] = 'login'
            st.rerun()

    with col2:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #28a745; min-height: 200px; text-align: center;"><h4>🚀 Seja Consultor</h4><p>Cadastre-se para utilizar nossas ferramentas de IA parlamentar.</p></div>', unsafe_allow_html=True)
        if st.button("CRIAR CONTA / CADASTRAR", key="btn_cad_home", use_container_width=True):
            st.session_state['tela'] = 'cadastro'
            st.rerun()

    with col3:
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #ffc107; min-height: 200px; text-align: center;"><h4>🛰️ Ecossistema</h4><p>Tecnologia e consultoria para captação estratégica.</p></div>', unsafe_allow_html=True)
        st.info("💡 Consultoria + Tecnologia")

def tela_cadastro():
    st.markdown("<h2 style='text-align: center; color: #28a745;'>🚀 Iniciar Nova Consultoria CoreGov</h2>", unsafe_allow_html=True)
    
    links_pagamento = {
        "BÁSICO": "https://mpago.la/1gf9ryq",
        "PREMIUM": "https://mpago.la/2CUKQgx"
    }

    if st.button("⬅️ Voltar para o Início"):
        st.session_state['tela'] = 'home'
        st.rerun()

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-top: 5px solid #6c757d; min-height: 250px;">
                <h4 style="color: #495057; margin:0;">🌱 PLANO BÁSICO (ESTADUAL)</h4>
                <p style="font-size: 13px; color: #666;">Consultoria estratégica para atuação regional.</p>
                <h3 style="color: #333; margin-top: 5px;">R$ 1.250,00 <small style="font-size: 12px;">/mês</small></h3>
                <ul style="font-size: 12px; color: #444;">
                    <li><b>Radar de Emendas:</b> Todo o estado escolhido</li>
                    <li>Monitoramento de Recursos 2026</li>
                    <li><b>Até 10 Revisões de Estatuto por IA</b></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown("""
            <div style="background-color: #e7f5ff; padding: 15px; border-radius: 10px; border-top: 5px solid #007bff; min-height: 250px;">
                <h4 style="color: #007bff; margin:0;">💎 PLANO PREMIUM (NACIONAL)</h4>
                <p style="font-size: 13px; color: #666;">Inteligência de dados para escala nacional.</p>
                <h3 style="color: #007bff; margin-top: 5px;">R$ 2.300,00 <small style="font-size: 12px; color: #333;">/mês</small></h3>
                <ul style="font-size: 12px; color: #444;">
                    <li><b>Acesso Nacional:</b> Todos os municípios e estados</li>
                    <li>Inteligência de Dados Prioritária</li>
                    <li><b>Até 15 Revisões de Estatuto por IA</b></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    st.write("\n")
    with st.form("form_registro_completo"):
        nome = st.text_input("Nome Completo")
        email = st.text_input("E-mail (Seu Login)")
        senha = st.text_input("Senha", type="password")
        plano = st.selectbox("Plano", ["BÁSICO", "PREMIUM"])
        local = st.text_input("Local de Atuação", placeholder="Ex: RJ ou Nacional")
        
        if st.form_submit_button("PRÓXIMO PASSO: CADASTRAR ➡️", use_container_width=True):
            if nome and email and senha:
                if salvar_cadastro_google_sheets([email, senha, 'pendente', plano, local, 0]):
                    st.success(f"✅ Cadastro realizado no ecossistema CoreGov!")
                    st.link_button(f"💳 IR PARA PAGAMENTO {plano}", links_pagamento[plano], use_container_width=True)
                else:
                    st.error("Erro ao salvar cadastro.")
            else:
                st.warning("Preencha todos os campos.")

def exibir_dashboard_boas_vindas(nome, plano, uso_revisor):
    st.markdown(f"### 👋 Bem-vindo ao CoreGov, {nome.capitalize()}!")
    col1, col2, col3 = st.columns(3)
    with col1: st.success("📊 Radar 2026 Ativo")
    with col2: st.info(f"📑 Revisor IA: {uso_revisor} usos")
    with col3: st.warning(f"🏆 Plano {plano}")
    st.divider()

# --- 4. EXECUÇÃO PRINCIPAL ---

st.set_page_config(page_title="CoreGov - Inteligência Governamental", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            exibir_home_publica()
        elif st.session_state['tela'] == 'cadastro':
            tela_cadastro()
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Login CoreGov")
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p):
                        st.rerun()
                    else: st.error("Acesso negado.")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
    else:
        with st.sidebar:
            st.title("CoreGov")
            user = st.session_state.get('usuario_nome', 'admin')
            st.info(f"👤 {user.upper()}")
            menu = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            if user.lower() == "admin": menu.append("🔧 Gestão Admin")
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        if escolha == "🚪 Sair":
            st.session_state.clear()
            st.session_state['logado'] = False
            st.session_state['tela'] = 'home'
            st.rerun()
        elif escolha == "🔧 Gestão Admin":
            st.title("🔧 Gestão Administrativa CoreGov")
            try:
                creds = Credentials.from_service_account_file('ponto-facial-oseiascarveng-cd7b1ab54295.json', scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
                client = gspread.authorize(creds)
                sh = client.open("ID_LICENÇAS")
                st.subheader("📝 Logs de Acesso")
                st.dataframe(pd.DataFrame(sh.worksheet("logs").get_all_records()))
                st.subheader("👥 Base de Usuários")
                st.dataframe(pd.DataFrame(sh.worksheet("usuario").get_all_records()))
            except Exception as e: st.error(f"Erro: {e}")
        elif escolha == "🏛️ Radar de Emendas": radar_emendas_2026.exibir_radar()
        elif escolha == "📊 Recursos 2026": recursos2026.exibir_recursos()
        elif escolha == "📜 Revisor de Estatuto": revisor_estatuto.exibir_revisor()
        else:
            exibir_dashboard_boas_vindas(user, st.session_state.get('usuario_plano', 'BÁSICO'), st.session_state.get('usuario_logado', {}).get('REVISOES_USADAS', 0))

if __name__ == "__main__":
    executar()
