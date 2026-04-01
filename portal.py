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
    
    if escolha == "📊 Recursos":
        st.title("📊 Monitoramento de Recursos")
        st.info("Este módulo está sendo integrado com a base de dados do Tesouro Nacional.")
        # Aqui você chamaria a função do módulo de recursos
        
    elif escolha == "🏛️ Radar de Emendas":
        # IMPORTANTE: Aqui chamamos a função que criamos no arquivo de emendas
        try:
            import radar_emendas_2026 as radar
            radar.executar()
        except ImportError:
            st.error("Módulo 'radar_emendas_2026.py' não encontrado no diretório.")
        except Exception as e:
            st.error(f"Erro ao carregar o Radar: {e}")
            
    elif escolha == "📜 Revisão de Estatuto":
        st.title("📜 Revisor de Estatutos (IA)")
        st.write("Suba o arquivo PDF do estatuto para análise de conformidade.")
        # Aqui viria o seu código de análise de texto/PDF
        
    elif escolha == "⚙️ Gestão Administrativa":
        st.title("⚙️ Configurações e Gestão")
        st.write("Espaço reservado para cadastro de clientes e controle de acessos.")
        
    elif escolha == "🚪 Sair":
        st.warning("Você solicitou o encerramento da sessão.")
        if st.button("Confirmar Saída"):
            st.write("Sessão encerrada com segurança. Até logo!")
            st.stop()

if __name__ == "__main__":
    executar()
