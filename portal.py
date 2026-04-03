import streamlit as st
import pandas as pd
import gdown
import os
import importlib
import gspread
import smtplib
from email.mime.text import MIMEText
import urllib.parse
from google.oauth2.service_account import Credentials

# --- 1. FUNÇÕES DE APOIO (CONEXÃO GOOGLE E NOTIFICAÇÕES) ---

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

def enviar_aviso_email(nome, plano, email_cliente):
    meu_email = "oseiasnepom@gmail.com" 
    minha_senha = "tukh raae ebnc dgoe" 
    
    msg = MIMEText(f"Olá Oseias!\n\nUm novo consultor acabou de se cadastrar:\n\nNome: {nome}\nPlano: {plano}\nE-mail: {email_cliente}\n\nVerifique a planilha ID_LICENÇAS para liberar o acesso.")
    msg['Subject'] = f"🚀 NOVO CADASTRO: {plano} - {nome}"
    msg['From'] = meu_email
    msg['To'] = meu_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(meu_email, minha_senha)
        server.sendmail(meu_email, meu_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

def gerar_link_whatsapp(nome, plano):
    texto = f"Olá Core Essence! Acabei de me cadastrar no Portal Radar 2026.\nNome: {nome}\nPlano Escolhido: {plano}.\nAguardo liberação!"
    texto_url = urllib.parse.quote(texto)
    return f"https://wa.me/5518991466238?text={texto_url}"

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

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Core Essence", page_icon="🛰️", layout="wide")

# --- 3. TELAS DO SISTEMA ---

def tela_cadastro():
    st.title("🚀 Cadastro de Novo Consultor")
    
    links_pagamento = {
        "BRONZE": "https://mpago.la/1gf9ryq",
        "PRATA": "https://mpago.la/1bGimm8",
        "OURO": "https://mpago.la/1x63i2w",
        "DIAMANTE": "https://mpago.la/2CUKQgx"
    }

    if 'cadastro_concluido' not in st.session_state:
        st.session_state['cadastro_concluido'] = False

    if st.button("⬅️ Voltar para o Início", key="btn_voltar_home_cad"):
        st.session_state['tela'] = 'home'
        st.session_state['cadastro_concluido'] = False
        st.rerun()

    if not st.session_state['cadastro_concluido']:
        st.write("Escolha seu plano e preencha os dados para solicitar seu acesso.")
        
        opcoes_planos = {
            "BRONZE: Acesso a até 03 Municípios + 05 Revisões": "BRONZE",
            "PRATA: Acesso a 01 Estado completo + 15 Revisões": "PRATA",
            "OURO: Acesso a 03 Estados completos + 50 Revisões": "OURO",
            "DIAMANTE: Acesso Nacional (Brasil) + 200 Revisões": "DIAMANTE"
        }
        
        escolha_visual = st.selectbox("Selecione o Plano Desejado:", list(opcoes_planos.keys()))
        plano_final = opcoes_planos[escolha_visual]

        if plano_final == "BRONZE":
            label_local = "📍 Liste as 03 Cidades de Interesse"
            placeholder_local = "Ex: Presidente Prudente, Álvares Machado..."
            tipo_consultor = "MUNICIPAL"
        elif plano_final in ["PRATA", "OURO"]:
            label_local = "📍 Liste os Estados (UF) de Interesse"
            placeholder_local = "Ex: SP, RJ, MG"
            tipo_consultor = "ESTADUAL"
        else:
            label_local = "📍 Localidade (Acesso Nacional Liberado)"
            placeholder_local = "Digite BRASIL ou deixe em branco"
            tipo_consultor = "NACIONAL"

        with st.form("form_dados_pessoais"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail (Seu futuro usuário)")
            senha = st.text_input("Crie uma Senha", type="password")
            localidade = st.text_input(label_local, placeholder=placeholder_local)
            
            st.warning(f"⚠️ Plano selecionado: **{plano_final}** ({tipo_consultor})")
            
            btn_enviar = st.form_submit_button("PRÓXIMO PASSO: PAGAMENTO ➡️")
            
            if btn_enviar:
                if nome and email and senha:
                    status_inicial = "pendente" 
                    novo_usuario = [email, senha, status_inicial, plano_final, tipo_consultor, localidade]
                    
                    if salvar_cadastro_google_sheets(novo_usuario):
                        enviar_aviso_email(nome, plano_final, email)
                        st.session_state['cadastro_concluido'] = True
                        st.session_state['plano_selecionado'] = plano_final
                        st.session_state['nome_temp'] = nome
                        st.rerun()
                    else:
                        st.error("Erro técnico ao salvar na planilha.")
                else:
                    st.error("Por favor, preencha Nome, E-mail e Senha.")
    else:
        st.success(f"✅ Quase lá, {st.session_state['nome_temp']}! Cadastro recebido.")
        st.subheader("💳 Ativação do Acesso")
        st.write(f"Para liberar seu plano **{st.session_state['plano_selecionado']}**, finalize o pagamento abaixo:")
        
        link_mp = links_pagamento.get(st.session_state['plano_selecionado'], "")
        st.link_button(f"👉 PAGAR PLANO {st.session_state['plano_selecionado']} NO MERCADO PAGO", link_mp, type="primary")
        
        st.info("💡 Após o pagamento, seu acesso será liberado em até 30 minutos.")
        link_zap = gerar_link_whatsapp(st.session_state['nome_temp'], st.session_state['plano_selecionado'])
        st.link_button("📱 JÁ PAGUEI? ENVIAR COMPROVANTE AGORA", link_zap)

# --- 4. NAVEGAÇÃO E LÓGICA PRINCIPAL ---

def executar():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.markdown("<h1 style='text-align: center;'>🛰️ Core Essence</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #555;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
            st.write("\n")
            
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                st.info("**Para nossos Consultores:**\n\n*Bem-vindo de volta ao centro da estratégia.*")
            with c_f2:
                st.success("**Para novos Membros:**\n\n*Transforme dados governamentais em faturamento real.*")
            with c_f3:
                st.warning("**Por que Core Essence?**\n\n*Não apenas monitore recursos, antecipe-se.*")

            st.markdown("---")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("👤 JÁ SOU CONSULTOR (LOGIN)", use_container_width=True, type="primary"):
                    st.session_state['tela'] = 'login'
                    st.rerun()
            with col_b2:
                if st.button("🚀 QUERO ME CADASTRAR AGORA", use_container_width=True):
                    st.session_state['tela'] = 'cadastro'
                    st.rerun()

        elif st.session_state['tela'] == 'cadastro':
            tela_cadastro()
            
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Acesso ao Portal")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
            with st.form("login_form"):
                u = st.text_input("Usuário (E-mail)")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p):
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos ou acesso ainda pendente.")

    else:
        # --- ÁREA LOGADA COM RECONHECIMENTO DE ADMIN ---
        with st.sidebar:
            st.title("Core Essence")
            plano = st.session_state.get('usuario_plano', 'BRONZE')
            usuario_atual = st.session_state.get('usuario_nome')
            
            st.info(f"🏆 Plano: {plano}")
            
            # Lista básica de módulos
            menu = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão"]
            
            # SE FOR O OSEIAS, ADICIONA GESTÃO
            if usuario_atual == "oseiasnepom@gmail.com":
                menu.append("🔧 Gestão Admin")
            
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        if escolha == "🚪 Sair":
            st.session_state.clear()
            st.rerun()
        
        elif escolha == "🔧 Gestão Admin":
            st.subheader("🔧 Painel de Controle - Administrador")
            st.write("Bem-vindo, Oseias. Use este espaço para gerenciar o portal.")
            st.warning("Módulo de ativação via App em desenvolvimento. Use a planilha Google para ativar usuários.")
            
        else:
            st.write(f"### Bem-vindo ao módulo {escolha}")
            st.info("Utilize o menu lateral para navegar entre as ferramentas de inteligência.")

if __name__ == "__main__":
    executar()
