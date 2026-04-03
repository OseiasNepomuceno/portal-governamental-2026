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

# --- 1. IMPORTAÇÃO DOS MÓDULOS ORIGINAIS (NOMES RESTAURADOS) ---
import radar_emendas_2026  # Antigo radar.py
import recursos2026        # Antigo recursos.py
import revisor_estatuto    # Antigo revisao.py

# --- 2. FUNÇÕES DE APOIO (CONEXÃO GOOGLE E NOTIFICAÇÕES) ---

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
    msg = MIMEText(f"Olá Oseias!\n\nUm novo consultor se cadastrou:\n\nNome: {nome}\nPlano: {plano}\nE-mail: {email_cliente}")
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

def gerar_link_whatsapp(nome, plano):
    texto = f"Olá Core Essence! Me cadastrei no Portal Radar 2026.\nNome: {nome}\nPlano: {plano}."
    return f"https://wa.me/5518991466238?text={urllib.parse.quote(texto)}"

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
                info_usuario['local_liberado'] = dados.get('LOCALIDADE', '')
                
                st.session_state['usuario_logado'] = info_usuario
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = dados.get('USUARIO', 'Consultor')
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BRONZE')).upper().strip()
                return True
        return False
    except: return False

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Core Essence", page_icon="🛰️", layout="wide")

# --- 4. TELAS DO SISTEMA ---

def tela_cadastro():
    st.title("🚀 Cadastro de Novo Consultor")
    links_pagamento = {"BRONZE": "https://mpago.la/1gf9ryq", "PRATA": "https://mpago.la/1bGimm8", "OURO": "https://mpago.la/1x63i2w", "DIAMANTE": "https://mpago.la/2CUKQgx"}

    if st.button("⬅️ Voltar para o Início"):
        st.session_state['tela'] = 'home'
        st.rerun()

    if not st.session_state.get('cadastro_concluido', False):
        opcoes = {"BRONZE: 03 Municípios": "BRONZE", "PRATA: 01 Estado": "PRATA", "OURO: 03 Estados": "OURO", "DIAMANTE: Nacional": "DIAMANTE"}
        escolha_v = st.selectbox("Selecione o Plano:", list(opcoes.keys()))
        plano_f = opcoes[escolha_v]
        
        with st.form("form_cadastro"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            local = st.text_input("Cidades ou Estados de interesse")
            if st.form_submit_button("PRÓXIMO PASSO: PAGAMENTO ➡️"):
                if nome and email and senha:
                    if salvar_cadastro_google_sheets([email, senha, 'pendente', plano_f, 'CONSULTOR', local]):
                        enviar_aviso_email(nome, plano_f, email)
                        st.session_state['cadastro_concluido'] = True
                        st.session_state['plano_selecionado'] = plano_f
                        st.session_state['nome_temp'] = nome
                        st.rerun()
                else: st.error("Preencha os campos obrigatórios.")
    else:
        st.success(f"✅ Cadastro recebido, {st.session_state['nome_temp']}!")
        st.link_button(f"👉 PAGAR PLANO {st.session_state['plano_selecionado']}", links_pagamento.get(st.session_state['plano_selecionado'], ""))
        st.info("Após o pagamento, seu acesso será liberado em até 30 min.")

# --- 5. NAVEGAÇÃO E LÓGICA PRINCIPAL ---

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.markdown("<h1 style='text-align: center;'>🛰️ Core Essence</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #555;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
            st.write("\n")
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: st.info("**Para nossos Consultores:**\n\n*Bem-vindo de volta.*")
            with c_f2: st.success("**Para novos Membros:**\n\n*Transforme dados em faturamento.*")
            with c_f3: st.warning("**Por que Core Essence?**\n\n*Antecipe-se aos recursos.*")
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("👤 JÁ SOU CONSULTOR (LOGIN)", use_container_width=True, type="primary"):
                st.session_state['tela'] = 'login'; st.rerun()
            if col_b2.button("🚀 QUERO ME CADASTRAR AGORA", use_container_width=True):
                st.session_state['tela'] = 'cadastro'; st.rerun()

        elif st.session_state['tela'] == 'cadastro': tela_cadastro()
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Acesso ao Portal")
            if st.button("⬅️ Voltar"): st.session_state['tela'] = 'home'; st.rerun()
            with st.form("login_form"):
                u = st.text_input("E-mail")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p): st.rerun()
                    else: st.error("Acesso incorreto ou pendente.")

    else:
        # --- ÁREA LOGADA ---
        with st.sidebar:
            st.title("Core Essence")
            plano = st.session_state.get('usuario_plano', 'BRONZE')
            usuario_atual = st.session_state.get('usuario_nome')
            st.info(f"🏆 Plano: {plano}")
            
            # Definição do Menu
            menu = ["📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto"]
            if usuario_atual == "oseiasnepom@gmail.com": 
                menu.append("🔧 Gestão Admin")
            menu.append("🚪 Sair")
            
            escolha = st.radio("Módulos:", menu)

        if escolha == "🚪 Sair":
            st.session_state.clear()
            st.rerun()
        
        elif escolha == "🔧 Gestão Admin":
            st.subheader("🔧 Painel de Controle - Administrador")
            try:
                scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
                creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
                client = gspread.authorize(creds)
                sheet = client.open("ID_LICENÇAS").worksheet("usuario")
                dados = sheet.get_all_records()
                df_gestao = pd.DataFrame(dados)
                if not df_gestao.empty:
                    pendentes = df_gestao[df_gestao['status'].astype(str).str.lower() == 'pendente']
                    if not pendentes.empty:
                        st.info(f"Existem {len(pendentes)} solicitações aguardando.")
                        for index, row in pendentes.iterrows():
                            with st.expander(f"Solicitação: {row['usuario']}"):
                                if st.button(f"✅ ATIVAR: {row['usuario']}", key=f"btn_{index}"):
                                    sheet.update_cell(index + 2, 3, "ativo")
                                    st.success("Liberado!"); st.rerun()
                    else: st.success("🎉 Nenhuma solicitação pendente!")
                st.markdown("---")
                st.write("### Lista Geral")
                st.dataframe(df_gestao)
            except Exception as e: 
                st.error(f"Erro na gestão: {e}")

        elif escolha == "🏛️ Radar de Emendas":
            radar_emendas_2026.exibir_radar() # Chama a função do arquivo original
            
        elif escolha == "📊 Recursos 2026":
            recursos2026.exibir_recursos()    # Chama a função do arquivo original

        elif escolha == "📜 Revisor de Estatuto":
            revisor_estatuto.exibir_revisor() # Chama a função do arquivo original

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    executar()
