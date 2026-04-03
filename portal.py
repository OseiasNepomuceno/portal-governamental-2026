import streamlit as st
import pandas as pd
import gdown
import os
import gspread
import smtplib
from email.mime.text import MIMEText
import urllib.parse
from google.oauth2.service_account import Credentials

# --- 1. IMPORTAÇÃO DOS MÓDULOS (Nomes sincronizados com os arquivos) ---
import radar_emendas_2026  
import recursos2026        
import revisor_estatuto    

# --- 2. FUNÇÕES DE APOIO ---

def salvar_cadastro_google_sheets(dados_cliente):
    # scope movido para dentro para evitar problemas de escopo global
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        if not os.path.exists(nome_da_chave):
            st.error(f"Arquivo de credenciais {nome_da_chave} não encontrado.")
            return False
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
        
        # Filtro de login robusto
        user_row = df[(df['USUARIO'].astype(str).str.strip() == str(usuario_digitado).strip()) & 
                      (df['SENHA'].astype(str).str.strip() == str(senha_digitada).strip())]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS', 'pendente')).lower().strip() == 'ativo':
                info_usuario = dados.to_dict()
                # Padronização de chaves para os módulos
                info_usuario['PLANO'] = str(dados.get('PLANO', 'BRONZE')).upper().strip()
                info_usuario['local_liberado'] = str(dados.get('LOCALIDADE', '')).upper().strip()
                
                st.session_state['usuario_logado'] = info_usuario
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = str(dados.get('USUARIO', ''))
                st.session_state['usuario_plano'] = info_usuario['PLANO']
                return True
        return False
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
        return False

# --- 3. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Core Essence | Inteligência Governamental", page_icon="🛰️", layout="wide")

# --- 4. TELAS ---

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
            email = st.text_input("E-mail (Será seu Login)")
            senha = st.text_input("Senha de Acesso", type="password")
            local = st.text_input("Localidades de Interesse (Cidades ou UFs)")
            
            if st.form_submit_button("PRÓXIMO PASSO:
