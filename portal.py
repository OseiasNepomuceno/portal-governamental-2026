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
import radar  # Importação do módulo do Radar

# --- 1. FUNÇÕES DE APOIO ---

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
        
        # Normaliza nomes das colunas para evitar erro de Maiúscula/Minúscula
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        u_col = 'USUARIO' if 'USUARIO' in df.columns else 'usuario'
        s_col = 'SENHA' if 'SENHA' in df.columns else 'senha'

        user_row = df[(df[u_col].astype(str).str.strip() == str(usuario_digitado).strip()) & 
                      (df[s_col].astype(str).str.strip() == str(senha_digitada).strip())]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            status = str(dados.get('STATUS', 'pendente')).lower().strip()
            
            if status == 'ativo':
                # AJUSTE AQUI: Mapeia LOCALIDADE para local_liberado para o radar.py funcionar
                info_usuario = dados.to_dict()
                info_usuario['local_liberado'] = dados.get('LOCALIDADE', '')
                
                st.session_state['usuario_logado'] = info_usuario
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = dados.get(u_col, 'Consultor')
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BRONZE')).upper().strip()
                return True
        return False
    except Exception as e:
        st.error(f"Erro no login: {e}")
        return False

# --- 2. CONFIGURAÇÃO ---
st.set_page_config(page_title="Core Essence", page_icon="🛰️", layout="wide")

# --- 3. TELAS ---

def tela_cadastro():
    st.title("🚀 Cadastro de Novo Consultor")
    links_pagamento = {"BRONZE": "https://mpago.la/1gf9ryq", "PRATA": "https://mpago.la/1bGimm8", "OURO": "https://mpago.la/1x63i2w", "DIAMANTE": "https://mpago.la/2CUKQgx"}
    
    if st.button("⬅️ Voltar"):
        st.session_state['tela'] = 'home'
        st.rerun()

    if not st.session_state.get('cadastro_concluido', False):
        opcoes = {"BRONZE: 03 Municípios": "BRONZE", "PRATA: 01 Estado": "PRATA", "OURO: 03 Estados": "OURO", "DIAMANTE: Nacional": "DIAMANTE"}
        escolha_visual = st.selectbox("Plano:", list(opcoes.keys()))
        plano_final = opcoes[escolha_visual]
        
        with st.form("form_cad"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            local = st.text_input("Localidade (Cidades ou UFs)")
            if st.form_submit_button("CADASTRAR E IR PARA PAGAMENTO"):
                if nome and email and senha:
                    if salvar_cadastro_google_sheets([email, senha, 'pendente', plano_final, 'CONSULTOR', local]):
                        enviar_aviso_email(nome, plano_final, email)
                        st.session_state['cadastro_concluido'] = True
                        st.session_state['plano_sel'] = plano_final
                        st.rerun()
    else:
        st.success("Cadastro Realizado!")
        st.link_button(f"PAGAR PLANO {st.session_state['plano_sel']}", links_pagamento.get(st.session_state['plano_sel'], ""))

# --- 4. LÓGICA PRINCIPAL ---

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'tela' not in st.session_state: st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.title("🛰️ Core Essence")
            col1, col2 = st.columns(2)
            if col1.button("LOGIN"): st.session_state['tela'] = 'login'; st.rerun()
            if col2.button("CADASTRO"): st.session_state['tela'] = 'cadastro'; st.rerun()
        elif st.session_state['tela'] == 'cadastro': tela_cadastro()
        elif st.session_state['tela'] == 'login':
            u = st.text_input("E-mail")
            p = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                if autenticar_usuario(u, p): st.rerun()
                else: st.error("Acesso negado ou pendente.")
    else:
        with st.sidebar:
            st.title("Core Essence")
            menu = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão"]
            if st.session_state.get('usuario_nome') == "oseiasnepom@gmail.com":
                menu.append("🔧 Gestão Admin")
            menu.append("🚪 Sair")
            escolha = st.radio("Módulos:", menu)

        if escolha == "🚪 Sair":
            st.session_state.clear(); st.rerun()
        elif escolha == "🔧 Gestão Admin":
            st.subheader("Painel Administrativo")
            # Código de gestão simplificado para o exemplo
            st.info("Área do administrador ativa.")
        elif escolha == "🏛️ Radar de Emendas":
            radar.exibir_radar()
        else:
            st.write(f"Bem-vindo ao módulo {escolha}")

if __name__ == "__main__":
    executar()
