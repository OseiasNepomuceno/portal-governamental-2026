import streamlit as st
import pandas as pd
import gdown
import os
import gspread
import smtplib
import unicodedata
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

    # Limites atualizados para 15 e 10
    limite_revisoes = 15 if plano == "PREMIUM" else 10
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

    with col3:
        st.markdown(
            f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; min-height: 150px;">
                <h4 style="margin: 0; color: #856404;">🏆 Plano {plano}</h4>
                <p style="font-size: 14px; color: #555; margin-top: 10px;">Sua licença de consultor está ativa e é válida por 30 dias.</p>
                <small>Expiração: <b>em 30 dias</b></small>
            </div>
            """, unsafe_allow_html=True
        )
    st.divider()

def registrar_log_acesso(nome, email, plano):
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
        
        # Limpeza de nomes de colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Filtro de usuário e senha
        user_row = df[(df['USUARIO'].astype(str).str.strip() == str(usuario_digitado).strip()) & 
                      (df['SENHA'].astype(str).str.strip() == str(senha_digitada).strip())]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS', 'pendente')).lower().strip() == 'ativo':
                info_usuario = dados.to_dict()
                info_usuario['PLANO'] = str(dados.get('PLANO', 'BÁSICO')).upper().strip()
                
                # BUSCA O SALDO NA COLUNA 6 (Índice 5 no DataFrame se for a 6ª coluna)
                # Como usamos df.iloc[0], acessamos pelo nome da coluna que o Pandas mapeou
                info_usuario['REVISOES_USADAS'] = dados.iloc[5] if len(dados) >= 6 else 0
                
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
    st.markdown("<h2 style='text-align: center; color: #28a745;'>🚀 Iniciar Nova Consultoria Especializada</h2>", unsafe_allow_html=True)
    
    links_pagamento = {
        "BÁSICO": "https://mpago.la/1gf9ryq",
        "PREMIUM": "https://mpago.la/2CUKQgx"
    }

    if st.button("⬅️ Voltar para o Início"):
        for chave in ['cadastro_concluido', 'plano_selecionado', 'nome_temp']:
            if chave in st.session_state:
                del st.session_state[chave]
        st.session_state['tela'] = 'home'
        st.rerun()

    if not st.session_state.get('cadastro_concluido', False):
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
        
        opcoes = {
            "PLANO BÁSICO (Monitoramento Estadual - R$ 1.250,00)": "BÁSICO", 
            "PLANO PREMIUM (Acesso Nacional - R$ 2.300,00)": "PREMIUM"
        }
        escolha_v = st.selectbox("Selecione o plano desejado:", list(opcoes.keys()))
        plano_f = opcoes[escolha_v]
        
        with st.form("form_cadastro_v2"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail (Login)")
            senha = st.text_input("Senha", type="password")
            local = st.text_input("Local de Atuação", placeholder="Ex: RJ ou Nacional")
            
            enviado = st.form_submit_button("PRÓXIMO PASSO: PAGAMENTO ➡️", use_container_width=True)
            
            if enviado:
                if nome and email and senha:
                    # Incluindo o '0' inicial para a coluna de REVISOES_USADAS (Coluna 6)
                    sucesso = salvar_cadastro_google_sheets([email, senha, 'pendente', plano_f, 'CONSULTOR', 0, local])
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
        st.write(f"Você selecionou o **PLANO {st.session_state['plano_selecionado']}**.")
        
        st.link_button(f"💳 CLIQUE AQUI PARA PAGAR", links_pagamento.get(st.session_state['plano_selecionado'], ""), use_container_width=True)
        
        if st.button("Finalizei o Pagamento / Voltar ao Início"):
            for chave in ['cadastro_concluido', 'plano_selecionado', 'nome_temp']:
                if chave in st.session_state:
                    del st.session_state[chave]
            st.session_state['tela'] = 'home'
            st.rerun()

        st.info("Após o pagamento e confirmação bancária, seu acesso será liberado.")

# --- 5. NAVEGAÇÃO E LÓGICA PRINCIPAL ---

def executar():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.markdown("<h1 style='text-align: center; color: #007bff;'>🛰️ Core Essence</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
            st.write("\n")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #007bff; min-height: 250px; text-align: center;">
                        <h4 style="color: #007bff;">👤 Já é Cliente?</h4>
                        <p style="font-size: 14px; color: #555;">Acesse sua área exclusiva para monitorar emendas e recursos em tempo real.</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("FAZER LOGIN", use_container_width=True, type="primary"):
                    st.session_state['tela'] = 'login'
                    st.rerun()

            with col2:
                st.markdown("""
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #28a745; min-height: 250px; text-align: center;">
                        <h4 style="color: #28a745;">🚀 Seja Consultor</h4>
                        <p style="font-size: 14px; color: #555;">Cadastre-se para utilizar nossas ferramentas de IA e transformar sua atuação parlamentar.</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("CRIAR CONTA / CADASTRAR", use_container_width=True):
                    st.session_state['tela'] = 'cadastro'
                    st.rerun()

            with col3:
                st.markdown("""
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-top: 5px solid #ffc107; min-height: 250px; text-align: center;">
                        <h4 style="color: #856404;">🛰️ Ecossistema</h4>
                        <p style="font-size: 14px; color: #555;">A Core Essence une tecnologia de ponta e consultoria humana para captação estratégica de recursos.</p>
                    </div>
                """, unsafe_allow_html=True)
                st.info("💡 Consultoria + Tecnologia")

            st.divider()

        elif st.session_state['tela'] == 'cadastro': 
            tela_cadastro()
            
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Acesso ao Portal")
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
        with st.sidebar:
            st.title("Core Essence")
            usuario_atual = st.session_state.get('usuario_nome', 'Consultor').upper()
            plano_atual = st.session_state.get('usuario_plano', 'BÁSICO').upper()
            info_user = st.session_state.get('usuario_logado', {})
            
            # Localidade
            local = info_user.get('LOCALIDADE') or info_user.get('LOCAL_LIBERADO') or "BR"

            st.info(f"👤 **LOGIN:** {usuario_atual}")
            st.success(f"🏆 **PLANO:** {plano_atual}")
            st.warning(f"📍 **LOCAL:** {str(local).upper()}")
            
            st.divider()
            
            menu = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            if usuario_atual.lower() == "oseiasnepom@gmail.com":
                menu.append("🔧 Gestão Admin")
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        if escolha == "🏠 Home":
            # Pega o saldo atualizado da sessão
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
