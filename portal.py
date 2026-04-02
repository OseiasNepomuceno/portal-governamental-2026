import streamlit as st
import pandas as pd
import gdown
import os
import importlib
import gspread
from google.oauth2.service_account import Credentials

# --- FUNÇÕES DE APOIO ---
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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Core Essence", page_icon="🛰️", layout="wide")

# --- TELAS ADICIONAIS ---
def tela_cadastro():
    st.title("🚀 Cadastro de Novo Consultor")
    st.write("Preencha os dados abaixo para solicitar seu acesso ao Radar.")
    
    if st.button("⬅️ Voltar para o Início"):
        st.session_state['tela'] = 'home'
        st.rerun()

    with st.form("form_cadastro_novo"):
        nome = st.text_input("Nome Completo")
        email = st.text_input("E-mail (Será seu usuário)")
        senha = st.text_input("Crie uma Senha", type="password")
        plano_desejado = st.selectbox("Escolha seu Plano", ["BRONZE", "PRATA", "OURO", "DIAMANTE"])
        localidade = st.text_input("Localidade de Interesse (Cidade ou UF)")
        
        btn_enviar = st.form_submit_button("FINALIZAR CADASTRO")
        
        if btn_enviar:
            if nome and email and senha:
                # Formato para a planilha: Usuario, Senha, Plano, Localidade, Status
                novo_usuario = [email, senha, plano_desejado, localidade, "pendente"]
                if salvar_cadastro_google_sheets(novo_usuario):
                    st.success("✅ Cadastro enviado com sucesso! Aguarde a liberação administrativa.")
                    st.info("Área de integração com pagamento em desenvolvimento.")
                else:
                    st.error("Erro ao salvar cadastro. Tente novamente mais tarde.")
            else:
                st.warning("Por favor, preencha todos os campos obrigatórios.")

# --- NAVEGAÇÃO PRINCIPAL ---
def executar():
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    if 'tela' not in st.session_state:
        st.session_state['tela'] = 'home'

    if not st.session_state['logado']:
        if st.session_state['tela'] == 'home':
            # --- HEADER DE IMPACTO ---
            st.markdown("<h1 style='text-align: center;'>🛰️ Core Essence</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #555;'>Inteligência Governamental Estratégica</h3>", unsafe_allow_html=True)
            st.write("\n")
            
            # --- AS 3 FRASES DE IMPACTO ---
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                st.info("**Para nossos Consultores:**\n\n*Bem-vindo de volta ao centro da estratégia. Sua inteligência de dados está sincronizada e pronta para novas oportunidades.*")
            with c_f2:
                st.success("**Para novos Membros:**\n\n*Você está a um passo de transformar dados governamentais em faturamento real. O acesso ao maior radar de recursos do país começa aqui.*")
            with c_f3:
                st.warning("**Por que ser Core Essence?**\n\n*Não apenas monitore, antecipe-se. No jogo do setor público, a Core Essence é a diferença entre quem busca informações e quem domina resultados.*")

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
            st.markdown("<p style='text-align: center; font-size: 0.8rem; color: gray;'>© 2026 Core Essence - Todos os direitos reservados.</p>", unsafe_allow_html=True)

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
                    else:
                        st.error("Usuário ou senha incorretos.")

        elif st.session_state['tela'] == 'cadastro':
            tela_cadastro()

    else:
        # --- PORTAL APÓS LOGIN ---
        with st.sidebar:
            st.title("Core Essence")
            plano = st.session_state.get('usuario_plano', 'BRONZE')
            user_raw = st.session_state.get('usuario_nome', 'Consultor')
            user_comparar = str(user_raw).lower().strip()
            st.info(f"🏆 Plano: {plano}")

            menu = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão de Estatuto", "🚪 Sair"]
            if user_comparar == "admin":
                menu.insert(3, "⚙️ Gestão Administrativa")
            
            escolha = st.sidebar.radio("Módulos:", menu)

        # --- REDIRECIONAMENTO DE MÓDULOS ---
        if escolha == "📊 Recursos":
            import recursos2026 as rec
            importlib.reload(rec)
            rec.exibir_radar()

        elif escolha == "🏛️ Radar de Emendas":
            import radar_emendas_2026 as radar
            importlib.reload(radar)
            radar.exibir_radar()

        elif escolha == "📜 Revisão de Estatuto":
            st.title("📜 Revisão de Estatuto")
            limite = {"BRONZE": 5, "PRATA": 15, "OURO": 50, "DIAMANTE": 200}.get(plano, 5)
            st.info(f"Seu plano **{plano}** permite {limite} revisões mensais.")
            st.write("---")
            st.subheader("Análise de Conformidade")
            arquivo = st.file_uploader("Arraste o arquivo do Estatuto (PDF)", type=["pdf"])
            if arquivo:
                st.success("Arquivo recebido! Iniciando pré-análise...")

        elif escolha == "⚙️ Gestão Administrativa":
            import gestao as adm
            importlib.reload(adm)
            adm.exibir_gestao()

        elif escolha == "🚪 Sair":
            st.session_state.clear()
            st.rerun()

# --- DISPARO DO APP ---
if __name__ == "__main__":
    executar()
