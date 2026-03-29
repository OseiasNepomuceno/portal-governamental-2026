import streamlit as st

# 1. Inicializa o estado de login se não existir
if "logado" not in st.session_state:
    st.session_state.logado = True # Começa logado para seu teste atual

# 2. Lógica do Botão Sair
if escolha == "🚪 Sair":
    st.session_state.logado = False # "Desliga" o sistema
    st.info("Sessão encerrada com segurança. Até logo, Oseias!")
    if st.button("Logar novamente"):
        st.session_state.logado = True
        st.rerun() # Reinicia o app
    st.stop()

# 3. Trava de Segurança: Se não estiver logado, não mostra o restante
if not st.session_state.logado:
    st.warning("Por favor, realize o login para acessar o portal.")
    if st.button("Ir para tela de Login"):
        st.session_state.logado = True
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
