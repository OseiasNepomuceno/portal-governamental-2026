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
    """Exibe os 03 cards de boas-vindas no topo da área logada"""
    st.markdown(f"### 👋 Bem-vindo, {nome.split('@')[0].capitalize()}!")
    
    col1, col2, col3 = st.columns(3)
    
    # Card 1: Radar de Emendas
    with col1:
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; min-height: 150px;">
                <h4 style="margin: 0; color: #007bff;">📊 Radar 2026</h4>
                <p style="font-size: 14px; color: #555; margin-top: 10px;">Acompanhamento estratégico de emendas e recursos governamentais.</p>
                <span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px;">ATIVO</span>
            </div>
            """, unsafe_allow_html=True
        )

    # Card 2: Revisor (Dinâmico com Limites)
    limite_revisoes = 150 if plano == "PREMIUM" else 50
    with col2:
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; min-height: 150px;">
                <h4 style="margin: 0; color: #28a745;">📑 Revisor IA</h4>
                <p style="font-size: 14px; color: #555; margin-top: 10px;">Análise de conformidade de estatutos via Gemini 1.5 Flash.</p>
                <small>Uso: <b>{uso_revisor}/{limite_revisoes}</b></small>
            </div>
            """, unsafe_allow_html=True
        )

    # Card 3: Status da Licença
    with col3:
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; min-height: 150px;">
                <h4 style="margin: 0; color: #856404;">🏆 Plano {plano}</h4>
                <p style="font-size: 14px; color: #555; margin-top: 10px;">Sua licença de consultor está ativa e vinculada ao curso SENAI IA.</p>
                <small>Expiração: <b>31/12/2026</b></small>
            </div>
            """, unsafe_allow_html=True
        )
    st.divider()

def registrar_log_acesso(nome, email, plano):
    """Grava o histórico de acessos na aba 'logs' da planilha Google Sheets"""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        if os.path.exists(nome_da_chave):
            creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
            client = gspread.authorize(creds)
            planilha = client.open("ID_LICENÇAS").worksheet("logs")
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            planilha.append_row([data_hora, nome, email, plano])
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
    except Exception as e:
        st.error(f"Erro ao acessar Google Sheets: {e}")
        return False

def enviar_aviso_email(nome, plano, email_cliente):
    meu_email = "oseiasnepom@gmail.com" 
    minha_senha = "tukh raae ebnc dgoe" 
    msg = MIMEText(f"Olá Oseias!\n\nNovo cadastro no Portal:\n\nNome: {nome}\nPlano: {plano}\nE-mail: {email_cliente}")
    msg['Subject'] = f"🚀 NOVO CADASTRO: {plano} - {nome}"
    msg['From'] = meu_email
    msg['To'] = meu_email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(meu_email, minha_senha)
        server.sendmail(meu_email, meu_email, msg.as_string())
        server.quit()
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
        
        user_row = df[(df['USUARIO'].astype(str).str.strip() == str(usuario_digitado).strip()) & 
                      (df['SENHA'].astype(str).str.strip() == str(senha_digitada).strip())]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS', 'pendente')).lower().strip() == 'ativo':
                info_usuario = dados.to_dict()
                info_usuario['PLANO'] = str(dados.get('PLANO', 'BRONZE')).upper().strip()
                # Pega revisões usadas (se a coluna existir)
                info_usuario['REVISOES_USADAS'] = dados.get('REVISOES_USADAS', 0)
                
                st.session_state['usuario_logado'] = info_usuario
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = str(dados.get('USUARIO', ''))
                st.session_state['usuario_plano'] = info_usuario['PLANO']
                
                registrar_log_acesso(st.session_state['usuario_nome'], usuario_digitado, info_usuario['PLANO'])
                return True
        return False
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return False

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Core Essence | Inteligência Governamental", page_icon="🛰️", layout="wide")

# --- 4. TELA DE CADASTRO ---
def tela_cadastro():
    st.title("🚀 Cadastro de Novo Consultor")
    links_pagamento = {
        "BRONZE": "https://mpago.la/1gf9ryq", 
        "PRATA": "https://mpago.la/1bGimm8", 
        "OURO": "https://mpago.la/1x63i2w", 
        "DIAMANTE": "https://mpago.la/2CUKQgx"
    }

    if st.button("⬅️ Voltar"):
        st.session_state['tela'] = 'home'
        st.rerun()

    if not st.session_state.get('cadastro_concluido', False):
        opcoes = {"BRONZE: 03 Municípios": "BRONZE", "PRATA: 01 Estado": "PRATA", "OURO: 03 Estados": "OURO", "DIAMANTE: Nacional": "DIAMANTE"}
        escolha_v = st.selectbox("Selecione seu Plano:", list(opcoes.keys()))
        plano_f = opcoes[escolha_v]
        
        with st.form("form_cadastro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail (Login)")
            senha = st.text_input("Senha", type="password")
            local = st.text_input("Localidades (Cidades ou UFs)")
            
            enviado = st.form_submit_button("PRÓXIMO PASSO: PAGAMENTO ➡️")
            
            if enviado:
                if nome and email and senha:
                    sucesso = salvar_cadastro_google_sheets([email, senha, 'pendente', plano_f, 'CONSULTOR', local])
                    if sucesso:
                        enviar_aviso_email(nome, plano_f, email)
                        st.session_state['cadastro_concluido'] = True
                        st.session_state['plano_selecionado'] = plano_f
                        st.session_state['nome_temp'] = nome
                        st.rerun()
                else:
                    st.error("Preencha todos os campos obrigatórios.")
    else:
        st.success(f"✅ Cadastro recebido, {st.session_state['nome_temp']}!")
        st.link_button(f"💳 PAGAR PLANO {st.session_state['plano_selecionado']}", links_pagamento.get(st.session_state['plano_selecionado'], ""), use_container_width=True)
        st.info("Após o pagamento, seu acesso será liberado em até 30 min.")

# --- 5. NAVEGAÇÃO E LÓGICA PRINCIPAL ---

def executar():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.markdown("<h1 style='text-align: center;'>🛰️ Core Essence</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("👤 LOGIN", use_container_width=True, type="primary"):
                st.session_state['tela'] = 'login'
                st.rerun()
            if c2.button("🚀 CADASTRAR", use_container_width=True):
                st.session_state['tela'] = 'cadastro'
                st.rerun()

        elif st.session_state['tela'] == 'cadastro': 
            tela_cadastro()
            
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Acesso")
            if st.button("⬅️ Voltar"): 
                st.session_state['tela'] = 'home'
                st.rerun()
            with st.form("login_form"):
                u = st.text_input("E-mail")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p): 
                        st.rerun()
                    else: 
                        st.error("Erro no login ou ativação pendente.")

    else:
        # --- ÁREA LOGADA ---
        with st.sidebar:
            st.title("Core Essence")
            
            # Dados do Usuário
            usuario_atual = st.session_state.get('usuario_nome', 'Consultor').upper()
            plano_atual = st.session_state.get('usuario_plano', 'BRONZE').upper()
            info_user = st.session_state.get('usuario_logado', {})
            
            # Recupera Localidade (Estado)
            local = info_user.get('LOCALIDADE') or info_user.get('LOCAL_LIBERADO') or "RJ"

            # EXIBIÇÃO ORGANIZADA
            st.info(f"👤 **LOGIN:** {usuario_atual}")
            st.success(f"🏆 **PLANO:** {plano_atual}")
            st.warning(f"📍 **LOCAL:** {str(local).upper()}")
            
            st.divider()
            
            menu = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            
            if usuario_atual.lower() == "oseiasnepom@gmail.com":
                menu.append("🔧 Gestão Admin")
            
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        # LÓGICA DE EXIBIÇÃO DE CONTEÚDO
        if escolha == "🏠 Home":
            # Exibe os Cards de Boas-Vindas
            uso_rev = info_user.get('REVISOES_USADAS', 0)
            exibir_dashboard_boas_vindas(usuario_atual, plano_atual, uso_rev)
            
        elif escolha == "🚪 Sair":
            st.session_state.clear()
            st.rerun()
            
        elif escolha == "🏛️ Radar de Emendas":
            radar_emendas_2026.exibir_radar()
            
        elif escolha == "📊 Recursos 2026":
            recursos2026.exibir_recursos()
            
        elif escolha == "📜 Revisor de Estatuto":
            revisor_estatuto.exibir_revisor()
            
        elif escolha == "🔧 Gestão Admin":
            st.title("🔧 Painel de Gestão")
            tab1, tab2 = st.tabs(["LOG_ACESSOS", "Configurações"])
            
            with tab1:
                try:
                    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                    creds = Credentials.from_service_account_file('ponto-facial-oseiascarveng-cd7b1ab54295.json', scopes=scope)
                    client = gspread.authorize(creds)
                    df_logs = pd.DataFrame(client.open("ID_LICENÇAS").worksheet("logs").get_all_records())
                    st.write("### Histórico de Acessos Recentes")
                    st.dataframe(df_logs, use_container_width=True)
                except:
                    st.warning("Verifique a aba 'logs' na sua planilha.")

if __name__ == "__main__":
    executar()
