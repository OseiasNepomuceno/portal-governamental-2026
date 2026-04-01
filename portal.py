import streamlit as st
import pandas as pd
import gdown
import os
import importlib

# --- 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira) ---
st.set_page_config(
    page_title="Core Essence - Portal de Gestão",
    page_icon="🛰️",
    layout="wide"
)

# --- 2. FUNÇÃO DE LOGIN E PLANOS ---
def autenticar_usuario(usuario_digitado, senha_digitada):
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_login.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        
        # Busca o usuário na planilha
        user_row = df[(df['usuario'].astype(str) == str(usuario_digitado)) & 
                      (df['senha'].astype(str) == str(senha_digitada))]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados['status']).lower() == 'ativo':
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = dados['usuario']
                st.session_state['usuario_plano'] = str(dados['plano']).upper()
                st.session_state['usuario_status'] = 'ativo'
                return True
            else:
                st.error("⚠️ Esta conta está EXPIRADA. Entre em contato com o suporte.")
        else:
            st.error("❌ Usuário ou senha incorretos.")
    except Exception as e:
        st.error(f"Erro ao conectar com base de dados: {e}")
    return False

# --- 3. INTERFACE DE LOGIN ---
if 'logado' not in st.session_state or not st.session_state['logado']:
    st.title("🛰️ Core Essence - Login")
    with st.form("login_form"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Acessar Portal")
        
        if entrar:
            if autenticar_usuario(u, p):
                st.success("Acesso liberado!")
                st.rerun()
    st.stop() # Interrompe aqui para não mostrar o portal sem login

# --- 4. SE CHEGOU AQUI, ESTÁ LOGADO. INICIA O PORTAL ---
def executar():
    with st.sidebar:
        st.title("Painel de Controle")
        
        # Tag Visual do Plano (Dinâmico conforme a planilha)
        plano = st.session_state.get('usuario_plano', 'BRONZE')
        st.info(f"🏆 Plano: {plano}")
        
        st.markdown("---")
        menu_opcoes = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão de Estatuto", "⚙️ Gestão Administrativa", "🚪 Sair"]
        escolha = st.radio("Selecione o Módulo:", menu_opcoes)
        
        st.markdown("---")
        st.caption(f"Logado como: {st.session_state.get('usuario_nome')}")

    # --- NAVEGAÇÃO ---
    if escolha == "📊 Recursos":
        try:
            import recursos2026 as rec
            importlib.reload(rec)
            rec.exibir_radar()
        except Exception as e:
            st.error(f"Erro no módulo Recursos: {e}")

    elif escolha == "🏛️ Radar de Emendas":
        try:
            import radar_emendas_2026 as radar
            importlib.reload(radar)
            radar.exibir_radar()
        except Exception as e:
            st.error(f"Erro no módulo Emendas: {e}")

    elif escolha == "📜 Revisão de Estatuto":
        st.title("📜 Revisão de Estatuto Inteligente")
        limite = {"BRONZE": 5, "PRATA": 15, "OURO": 50, "DIAMANTE": 200}.get(plano, 5)
        st.info(f"Seu plano {plano} permite {limite} revisões mensais.")
        st.file_uploader("Carregar documento (PDF)", type=["pdf"])

    elif "Gestão" in escolha:
        try:
            import gestao as adm
            importlib.reload(adm)
            adm.exibir_gestao()
        except Exception as e:
            st.error(f"Erro no módulo Gestão: {e}")

    elif escolha == "🚪 Sair":
        st.session_state['logado'] = False
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    executar()
