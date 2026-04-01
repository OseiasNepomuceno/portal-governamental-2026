import streamlit as st
import pandas as pd
import gdown
import os
import importlib
import gspread
from google.oauth2.service_account import Credentials

def salvar_cadastro_google_sheets(dados_cliente):
    """
    Função para salvar os dados do formulário na aba 'usuario' da planilha
    """
    # Escopos de permissão
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    try:
        # USA O NOME EXATO DO SEU ARQUIVO .JSON
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        
        creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha ID_LICENÇAS
        # Se a aba de usuários não for a primeira, mude .sheet1 para .worksheet("usuario")
        planilha = client.open("ID_LICENÇAS").sheet1
        
        # Adiciona a linha com os dados do novo consultor
        planilha.append_row(dados_cliente)
        return True
    except Exception as e:
        st.error(f"Erro técnico ao acessar a planilha: {e}")
        return False
# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Core Essence - Portal de Gestão",
    page_icon="🛰️",
    layout="wide"
)

# --- 2. FUNÇÃO DE LOGIN ---
def autenticar_usuario(usuario_digitado, senha_digitada):
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_login.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        
        user_row = df[(df['usuario'].astype(str).str.strip() == str(usuario_digitado).strip()) & 
                      (df['senha'].astype(str).str.strip() == str(senha_digitada).strip())]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            plano_bruto = dados.get('PLANO', dados.get('plano', 'BRONZE'))
            status_bruto = dados.get('STATUS', dados.get('status', 'ativo'))

            if str(status_bruto).lower().strip() == 'ativo':
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = dados.get('usuario', 'Consultor')
                st.session_state['usuario_plano'] = str(plano_bruto).upper().strip()
                return True
            else:
                st.error("⚠️ Esta conta está EXPIRADA.")
        else:
            st.error("❌ Usuário ou senha incorretos.")
    except Exception as e:
        st.error(f"Erro ao conectar com base de dados: {e}")
    return False

# --- 3. TELA DE CADASTRO (A QUE VOCÊ PEDIU) ---
def tela_cadastro():
    st.title("📝 Cadastro de Consultor - Core Essence")
    st.write("Escolha seu plano e área de atuação.")
    
    if st.button("⬅️ Voltar para o Início"):
        st.session_state['tela'] = 'home'
        st.rerun()

    st.markdown("---")
    
    # 1. Seleção de Plano FORA do formulário para permitir atualização em tempo real
    planos = [
        "BRONZE - R$ 300,00/mês",
        "PRATA - R$ 800,00/mês",
        "OURO - R$ 2.000,00/mês",
        "DIAMANTE - R$ 5.000,00/mês"
    ]
    escolha = st.selectbox("Selecione seu Plano de Atuação:", planos)

    # 2. Mensagem Dinâmica que muda IMEDIATAMENTE
    if "BRONZE" in escolha:
        st.info("🎯 **PLANO BRONZE:** Você terá acesso a **03 cidades** específicas dentro de 01 estado + **05 Revisões** de Estatuto Inteligente.")
    elif "PRATA" in escolha:
        st.info("🥈 **PLANO PRATA:** Você terá acesso a **01 Estado completo** (todas as cidades) + **15 Revisões** de Estatuto Inteligente.")
    elif "OURO" in escolha:
        st.info("🥇 **PLANO OURO:** Você terá acesso a **03 Estados completos** (todas as cidades) + **50 Revisões** de Estatuto Inteligente.")
    elif "DIAMANTE" in escolha:
        st.success("💎 **PLANO DIAMANTE:** Acesso **NACIONAL TOTAL** (Todos os Estados + DF) + **200 Revisões** de Estatuto Inteligente.")

    # 3. Formulário para os dados e campos específicos
    with st.form("detalhes_cadastro"):
        nome = st.text_input("Nome Completo")
        whatsapp = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail Profissional")

        # Campos de texto que também mudam conforme a escolha acima
        if "BRONZE" in escolha:
            st.text_input("Qual o Estado (UF)?")
            st.text_area("Liste as 03 cidades desejadas:")
        elif "PRATA" in escolha:
            st.text_input("Qual o Estado (UF) deseja liberar?")
        elif "OURO" in escolha:
            st.text_area("Quais os 03 Estados (UF) deseja liberar?")
        elif "DIAMANTE" in escolha:
            st.write("✅ Seu acesso será configurado como Master Nacional.")

       if st.form_submit_button("GERAR MEU ACESSO"):
            if nome and whatsapp and email:
                # Prepara a lista de dados para enviar à planilha
                # Ordem: usuario, senha, status, PLANO, nome_completo, whatsapp, email
                # DICA: Definimos a senha inicial como os 4 últimos dígitos do WhatsApp
                senha_inicial = str(whatsapp)[-4:]
                
                novos_dados = [
                    email,           # usuario (será o email)
                    senha_inicial,   # senha
                    "pendente",      # status (fica pendente até você confirmar o PIX)
                    escolha.split('-')[0].strip(), # PLANO (Bronze, Prata, etc)
                    nome,            # Nome Completo
                    whatsapp,        # Contato
                    email            # Email de registro
                ]
                
                with st.spinner("Processando seu cadastro..."):
                    sucesso = salvar_cadastro_google_sheets(novos_dados)
                
                if sucesso:
                    st.balloons()
                    st.success(f"🚀 Excelente, {nome}! Seus dados foram salvos.")
                    st.markdown(f"""
                    ### 💳 Próximo Passo: Pagamento
                    Para liberar seu login agora, realize o PIX do valor: **{escolha.split('-')[1]}**
                    
                    **Chave PIX:** `SUA_CHAVE_AQUI`
                    
                    *Seu login será seu e-mail e sua senha temporária são os 4 últimos dígitos do seu WhatsApp.*
                    """)
            else:
                st.warning("Por favor, preencha todos os campos obrigatórios.")
# --- 4. LÓGICA DE NAVEGAÇÃO PRINCIPAL ---
def executar():
    # Inicializa variáveis de controle
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'home'

    # Fluxo de Telas
    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            st.title("🛰️ Core Essence - Inteligência Governamental")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👤 JÁ SOU CONSULTOR (LOGIN)", use_container_width=True):
                    st.session_state['tela'] = 'login'
                    st.rerun()
            with col2:
                if st.button("🚀 QUERO ME CADASTRAR", use_container_width=True):
                    st.session_state['tela'] = 'cadastro'
                    st.rerun()
        
        elif st.session_state['tela'] == 'login':
            st.title("🔑 Acesso ao Portal")
            if st.button("⬅️ Voltar"):
                st.session_state['tela'] = 'home'
                st.rerun()
            
            with st.form("login_form"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p):
                        st.rerun()
        
        elif st.session_state['tela'] == 'cadastro':
            tela_cadastro()

    else:
        # --- PORTAL APÓS LOGIN ---
        with st.sidebar:
            st.title("Core Essence")
            plano = st.session_state.get('usuario_plano', 'BRONZE')
            st.info(f"🏆 Plano: {plano}")
            menu = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão de Estatuto", "⚙️ Gestão Administrativa", "🚪 Sair"]
            escolha = st.radio("Módulos:", menu)
            st.caption(f"Usuário: {st.session_state.get('usuario_nome')}")

        if escolha == "📊 Recursos":
            try:
                import recursos2026 as rec
                importlib.reload(rec)
                rec.exibir_radar()
            except Exception as e: st.error(f"Erro: {e}")

        elif escolha == "🏛️ Radar de Emendas":
            try:
                import radar_emendas_2026 as radar
                importlib.reload(radar)
                radar.exibir_radar()
            except Exception as e: st.error(f"Erro: {e}")

        elif escolha == "📜 Revisão de Estatuto":
            st.title("📜 Revisão de Estatuto")
            limite = {"BRONZE": 5, "PRATA": 15, "OURO": 50, "DIAMANTE": 200}.get(plano, 5)
            st.info(f"Limite: {limite} revisões.")
            st.file_uploader("Upload PDF", type=["pdf"])

        elif "Gestão" in escolha:
            try:
                import gestao as adm
                importlib.reload(adm)
                adm.exibir_gestao()
            except Exception as e: st.error(f"Erro: {e}")

        elif escolha == "🚪 Sair":
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    executar()
