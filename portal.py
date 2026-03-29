import streamlit as st
import pandas as pd

# --- FUNÇÃO PARA VERIFICAR ACESSO NA PLANILHA ---
def verificar_licenca(user_input, pass_input):
    try:
        # Usa o gdown ou o link direto de exportação CSV da sua planilha
        sheet_id = st.secrets["ID_LICENCAS"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_licencas = pd.read_csv(url)
        
        # Procura o usuário na planilha
        usuario_db = df_licencas[df_licencas['usuario'] == user_input]
        
        if not usuario_db.empty:
            senha_correta = str(usuario_db.iloc[0]['senha'])
            status = str(usuario_db.iloc[0]['status']).lower()
            
            if pass_input == senha_correta and status == "ativo":
                return True, "Sucesso"
            elif status == "expirado":
                return False, "Sua licença expirou. Entre em contato para renovar."
        
        return False, "Usuário ou senha incorretos."
    except Exception as e:
        return False, f"Erro de conexão com o servidor de licenças: {e}"

# --- TELA DE LOGIN ATUALIZADA ---
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

# --- SE CHEGOU AQUI, O USUÁRIO ESTÁ LOGADO ---
# Menu Lateral
st.sidebar.image("logo.png", width=150)
st.sidebar.title("💎 CORE ESSENCE")
menu = ["📊 Radar de Recursos 2026", "📈 Radar de Emendas", "📑 Revisor de Estatuto (MROSC)", "🚪 Sair"]
escolha = st.sidebar.radio("Navegação:", menu)

# Lógica do Botão Sair
if escolha == "🚪 Sair":
    st.session_state.logado = False
    st.info("Sessão encerrada com segurança.")
    if st.button("Voltar para a tela de Login"):
        st.rerun()
    st.stop()


# --- LÓGICA DE NAVEGAÇÃO (CHAMANDO OS OUTROS ARQUIVOS) ---

# --- LÓGICA DE NAVEGAÇÃO SEGURA ---

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

elif escolha == "🚪 Sair":
    st.info("Sessão encerrada com segurança. Até logo, Oseias!")
    st.stop()
