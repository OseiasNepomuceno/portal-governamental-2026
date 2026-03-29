import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="CORE ESSENCE - Portal 2026", layout="wide", page_icon="💎")

# --- CSS PROFISSIONAL E VISÍVEL ---
hide_st_style = """
            <style>
            /* Esconde o menu de 3 linhas e o rodapé padrão */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Esconde a barra de ferramentas superior (Deploy, Edit) */
            header {visibility: hidden;}
            [data-testid="stHeader"] {display: none;}
            
            /* Remove o espaço em branco exagerado no topo */
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }

            /* Garante que os títulos e textos fiquem visíveis */
            h1, h2, h3, p, span {
                visibility: visible !important;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ... Resto do seu código (Função de licença, Login, etc) ...


# --- FUNÇÃO PARA VERIFICAR ACESSO NA PLANILHA ---
def verificar_licenca(user_input, pass_input):
    try:
        sheet_id = st.secrets["ID_LICENCAS"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_licencas = pd.read_csv(url)
        
        usuario_db = df_licencas[df_licencas['usuario'].astype(str) == str(user_input)]
        
        if not usuario_db.empty:
            senha_correta = str(usuario_db.iloc[0]['senha'])
            status = str(usuario_db.iloc[0]['status']).lower()
            
            if str(pass_input) == senha_correta and status == "ativo":
                return True, "Sucesso"
            elif status == "expirado":
                return False, "Sua licença expirou. Entre em contato para renovar."
        
        return False, "Usuário ou senha incorretos."
    except Exception as e:
        return False, f"Erro de conexão com o servidor de licenças: {e}"

# --- INICIALIZAÇÃO DO ESTADO ---
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- TELA DE LOGIN ---
def tela_de_login():
    st.title("🔐 CORE ESSENCE - Gestão de Acessos")
    with st.form("login_form"):
        u = st.text_input("Usuário").strip()
        p = st.text_input("Senha", type="password").strip()
        if st.form_submit_button("Acessar Portal"):
            autorizado, mensagem = verificar_licenca(u, p)
            if autorizado:
                st.session_state.logado = True
                st.rerun()
            else:
                st.error(mensagem)

# --- TRAVA DE SEGURANÇA ---
if not st.session_state.logado:
    tela_de_login()
    st.stop()

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ LOGADO ---
# Menu Lateral
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")
menu = ["📊 Radar de Recursos 2026", "📈 Radar de Emendas", "📑 Revisor de Estatuto (MROSC)", "🚪 Sair"]
escolha = st.sidebar.radio("Navegação:", menu)

# --- LÓGICA DO BOTÃO SAIR (CORRIGIDA) ---
if escolha == "🚪 Sair":
    st.session_state.logado = False
    st.info("Sessão encerrada com segurança. Até logo!")
    
    if st.button("Voltar para a tela de Login"):
        st.session_state.clear() # Limpa TUDO para garantir o reset
        st.rerun()
    
    st.stop()

# --- NAVEGAÇÃO DOS MÓDULOS ---
if escolha == "📊 Radar de Recursos 2026":
    try:
        import recursos2026
        recursos2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar Radar de Recursos: {e}")

elif escolha == "📈 Radar de Emendas":
    try:
        import radar_emendas_2026
        radar_emendas_2026.executar()
    except Exception as e:
        st.error(f"Erro ao carregar Radar de Emendas: {e}")

elif escolha == "📑 Revisor de Estatuto (MROSC)":
    try:
        import revisor_estatuto
        revisor_estatuto.executar()
    except Exception as e:
        st.error(f"Erro ao carregar Revisor de Estatuto: {e}")
