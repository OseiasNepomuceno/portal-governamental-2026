import streamlit as st

# Importe aqui os seus módulos (certifique-se de que os nomes dos arquivos estão corretos)
# import radar_emendas_2026 as emendas
# import revisor_estatuto as estatuto

def executar():
    # Configuração da página (deve ser a primeira instrução de UI)
    st.set_page_config(
        page_title="Core Essence - Portal de Gestão",
        page_icon="🛰️",
        layout="wide"
    )

    # --- BARRA LATERAL: MENU DE NAVEGAÇÃO ---
    with st.sidebar:
        st.image("https://via.placeholder.com/150", caption="CORE ESSENCE v1.0") # Substitua pela sua logo se tiver
        st.title("Painel de Controle")
        st.markdown("---")
        
        # Menu Principal
        menu_opcoes = [
            "📊 Recursos", 
            "🏛️ Radar de Emendas", 
            "📜 Revisão de Estatuto", 
            "⚙️ Gestão Administrativa", 
            "🚪 Sair"
        ]
        
        escolha = st.radio("Selecione o Módulo:", menu_opcoes)
        
        st.markdown("---")
        st.caption("Usuário: Oseias | Plano: Professional")

    # --- LÓGICA DE EXIBIÇÃO DE CONTEÚDO ---
    
    # --- LÓGICA DE NAVEGAÇÃO ---
   # --- LÓGICA DE NAVEGAÇÃO ---
    if escolha == "📊 Recursos":
        try:
            # Importa o arquivo específico recursos2026.py
            import recursos2026 as rec
            # Chama a função que criamos lá dentro
            rec.exibir_radar() 
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo recursos2026.py: {e}")
            st.info("Verifique se o nome do arquivo no GitHub está exatamente como 'recursos2026.py'")

    elif escolha == "🏛️ Radar de Emendas":
        try:
            import radar_emendas_2026 as radar
            radar.exibir_radar() 
        except Exception as e:
            st.error(f"Erro ao carregar módulo: {e}")

    elif escolha == "📜 Revisão de Estatuto":
        # ... resto do seu código ...
        st.title("📜 Revisão de Estatuto")
        st.write("Área de análise de documentos.")

    elif escolha == "⚙️ Gestão":
        st.title("⚙️ Gestão Administrativa")
        st.write("Configurações do sistema.")

    elif escolha == "🚪 Sair":
        st.warning("Encerrando sessão...")
        st.stop()
if __name__ == "__main__":
    executar()
