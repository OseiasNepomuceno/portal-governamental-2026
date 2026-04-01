import streamlit as st
import pandas as pd
import gdown
import os
import importlib

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

    with st.form("form_premium"):
        nome = st.text_input("Nome Completo")
        whatsapp = st.text_input("WhatsApp (com DDD)")
        email = st.text_input("E-mail")
        
        planos = [
            "BRONZE - R$ 300,00/mês",
            "PRATA - R$ 800,00/mês",
            "OURO - R$ 2.000,00/mês",
            "DIAMANTE - R$ 5.000,00/mês"
        ]
        escolha = st.selectbox("Selecione seu Plano:", planos)

        # Campos dinâmicos
        if "BRONZE" in escolha:
            st.info("🎯 Bronze: 03 cidades + 05 Revisões")
            st.text_input("Estado (UF):")
            st.text_area("Quais as 03 cidades?")
        elif "PRATA" in escolha:
            st.info("🥈 Prata: 01 Estado completo + 15 Revisões")
            st.text_input("Qual Estado (UF)?")
        elif "OURO" in escolha:
            st.info("🥇 Ouro: 03 Estados completos + 50 Revisões")
            st.text_area("Quais os 03 Estados (UF)?")
        elif "DIAMANTE" in escolha:
            st.success("💎 Diamante: Nacional Total + 200 Revisões")

        if st.form_submit_button("GERAR ACESSO E PAGAMENTO"):
            st.success("✅ Cadastro pré-aprovado! Realize o PIX para liberar.")
            st.code("CHAVE-PIX-AQUI", language="text")
            st.info("Envie o comprovante para o suporte.")

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
