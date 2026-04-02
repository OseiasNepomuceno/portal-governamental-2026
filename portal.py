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
        planilha = client.open("ID_LICENÇAS").worksheet("usuario")
        
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

# --- 2. FUNÇÃO DE LOGIN ATUALIZADA ---
def autenticar_usuario(usuario_digitado, senha_digitada):
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_login.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        
        # Limpeza básica para evitar erros de espaços em branco
        df['usuario'] = df['usuario'].astype(str).str.strip()
        df['senha'] = df['senha'].astype(str).str.strip()

        user_row = df[(df['usuario'] == str(usuario_digitado).strip()) & 
                      (df['senha'] == str(senha_digitada).strip())]
        
        if not user_row.empty:
            # Pega a linha inteira do usuário
            dados = user_row.iloc[0]
            
            status_bruto = dados.get('STATUS', dados.get('status', 'ativo'))

            if str(status_bruto).lower().strip() == 'ativo':
                # --- AQUI ESTÁ A ALTERAÇÃO CRUCIAL ---
                # Salvamos a linha inteira (incluindo a nova coluna local_liberado)
                st.session_state['usuario_logado'] = dados.to_dict() 
                
                # Mantemos as variáveis antigas para não quebrar outras partes do código
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = dados.get('usuario', 'Consultor')
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BRONZE')).upper().strip()
                
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
    
    planos = [
        "BRONZE - R$ 300,00/mês",
        "PRATA - R$ 800,00/mês",
        "OURO - R$ 2.000,00/mês",
        "DIAMANTE - R$ 5.000,00/mês"
    ]
    escolha = st.selectbox("Selecione seu Plano de Atuação:", planos)

    if "BRONZE" in escolha:
        st.info("🎯 **PLANO BRONZE:** Acesso a 03 cidades + 05 Revisões.")
    elif "PRATA" in escolha:
        st.info("🥈 **PLANO PRATA:** Acesso a 01 Estado completo + 15 Revisões.")
    elif "OURO" in escolha:
        st.info("🥇 **PLANO OURO:** Acesso a 03 Estados completos + 50 Revisões.")
    elif "DIAMANTE" in escolha:
        st.success("💎 **PLANO DIAMANTE:** Acesso NACIONAL TOTAL + 200 Revisões.")

    # TUDO DAQUI PARA BAIXO PRECISA ESTAR COM 1 TAB (OU 4 ESPAÇOS) DE RECUO DENTRO DO WITH
    with st.form("detalhes_cadastro"):
        nome = st.text_input("Nome Completo")
        whatsapp = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail Profissional")

        if "BRONZE" in escolha:
            st.text_input("Qual o Estado (UF)?")
            st.text_area("Liste as 03 cidades desejadas:")
        elif "PRATA" in escolha:
            st.text_input("Qual o Estado (UF) deseja liberar?")
        elif "OURO" in escolha:
            st.text_area("Quais os 03 Estados (UF) deseja liberar?")
        elif "DIAMANTE" in escolha:
            st.write("✅ Seu acesso será configurado como Master Nacional.")

        # O botão precisa estar EXATAMENTE na mesma linha vertical do 'nome = ...'
        submit = st.form_submit_button("GERAR MEU ACESSO")

        if submit:
            if nome and whatsapp and email:
                # Prepara os dados para a planilha
                senha_inicial = str(whatsapp)[-4:]
                novos_dados = [
                    email, 
                    senha_inicial, 
                    "pendente", 
                    escolha.split('-')[0].strip(),
                    nome, 
                    whatsapp, 
                    email
                ]
                
                with st.spinner("Salvando seus dados..."):
                    sucesso = salvar_cadastro_google_sheets(novos_dados)
                
                if sucesso:
                    st.balloons()
                    st.success(f"🚀 Excelente, {nome}! Cadastro salvo com sucesso.")
                    
                    # Criando a mensagem personalizada para o seu WhatsApp
                    # Substitua pelo SEU número com DDD (ex: 5518999999999)
                    seu_numero = "5518991466238" 
                    mensagem_zap = f"Olá Core Essence, acabei de me cadastrar no Plano {escolha.split('-')[0].strip()}. Segue o comprovante!"
                    
                    # Formata o link para o WhatsApp
                    link_whatsapp = f"https://wa.me/{seu_numero}?text={requests.utils.quote(mensagem_zap)}"
                    
                    st.markdown(f"### 💳 Próximo Passo: Pagamento")
                    st.info("Para liberar seu acesso agora, realize o PIX e clique no botão abaixo para me enviar o comprovante.")
                    
                    # Botão visual para o WhatsApp
                    st.link_button("📲 ENVIAR COMPROVANTE VIA WHATSAPP", link_whatsapp)
                    
                    st.code("65919850000133", language="text")
            else:
                st.warning("Por favor, preencha todos os campos.")
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
