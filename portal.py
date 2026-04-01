# Portal atualizado com Gestão de Planos - 01/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

# --- FUNÇÃO PARA BUSCAR DADOS DO USUÁRIO NO DRIVE ---
def validar_usuario_plano():
    """Busca na planilha ID_LICENÇAS o plano do usuário logado"""
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_temp.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        # Simulando a busca pelo usuário atual (Oseias)
        # Em um sistema real, aqui compararíamos com o login efetuado
        dados = df[df['usuario'].str.lower() == "oseias"].iloc[0]
        
        # Salva na sessão para todos os módulos usarem
        st.session_state['usuario_nome'] = dados['usuario']
        st.session_state['usuario_plano'] = str(dados['plano']).upper()
        st.session_state['usuario_status'] = str(dados['status']).lower()
    except Exception as e:
        # Fallback caso a planilha falhe (Garante que o portal não quebre)
        st.session_state['usuario_nome'] = "Oseias"
        st.session_state['usuario_plano'] = "BRONZE" 
        st.session_state['usuario_status'] = "ativo"

def executar():
    # 1. Configuração da página
    st.set_page_config(
        page_title="Core Essence - Portal de Gestão",
        page_icon="🛰️",
        layout="wide"
    )

    # 2. Inicializa a sessão com o Plano se ainda não existir
    if 'usuario_plano' not in st.session_state:
        validar_usuario_plano()

    # --- BARRA LATERAL: MENU DE NAVEGAÇÃO ---
    with st.sidebar:
        st.image("https://via.placeholder.com/150", caption="CORE ESSENCE v1.0")
        st.title("Painel de Controle")
        
        # Identificador Visual do Plano
        plano = st.session_state.get('usuario_plano', 'BRONZE')
        cores = {"BRONZE": "#CD7F32", "PRATA": "#C0C0C0", "OURO": "#FFD700", "DIAMANTE": "#B9F2FF"}
        cor_plano = cores.get(plano, "#FFFFFF")
        
        st.markdown(f"""
            <div style="background-color:{cor_plano}; padding:10px; border-radius:10px; text-align:center;">
                <b style="color:black;">PLANO {plano}</b>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        menu_opcoes = [
            "📊 Recursos", 
            "🏛️ Radar de Emendas", 
            "📜 Revisão de Estatuto", 
            "⚙️ Gestão Administrativa", 
            "🚪 Sair"
        ]
        
        escolha = st.radio("Selecione o Módulo:", menu_opcoes)
        
        st.markdown("---")
        st.caption(f"Usuário: {st.session_state.get('usuario_nome')} | Status: {st.session_state.get('usuario_status').upper()}")

    # --- LÓGICA DE NAVEGAÇÃO ---
    
    if escolha == "📊 Recursos":
        try:
            import recursos2026 as rec
            # Passamos o plano para o módulo saber o que filtrar
            rec.exibir_radar() 
        except Exception as e:
            st.error(f"Erro ao carregar Recursos: {e}")

    elif escolha == "🏛️ Radar de Emendas":
        try:
            import radar_emendas_2026 as radar
            radar.exibir_radar() 
        except Exception as e:
            st.error(f"Erro ao carregar módulo: {e}")

    elif escolha == "📜 Revisão de Estatuto":
        # Trava de limite de revisões baseada no Plano
        limites = {"BRONZE": 5, "PRATA": 15, "OURO": 50, "DIAMANTE": 200}
        limite_atual = limites.get(plano, 5)
        
        st.title("📜 Revisor Inteligente")
        st.info(f"Seu plano **{plano}** permite até **{limite_atual}** revisões profissionais.")
        
        # Simulação de contador (você pode salvar isso na sua planilha de LOG_ACESSOS)
        contador = 0 
        
        if contador >= limite_atual:
            st.error("❌ Limite de revisões atingido! Faça upgrade para o Plano Diamante.")
            if st.button("🚀 Upgrade para DIAMANTE"):
                st.write("Redirecionando para consultoria comercial...")
        else:
            # Interface do Revisor
            arquivo_estatuto = st.file_uploader("Carregar Estatuto", type=["pdf"])
            if arquivo_estatuto:
                st.success("Análise liberada!")

    elif "Gestão" in escolha:
        try:
            import gestao as adm
            import importlib
            importlib.reload(adm)
            adm.exibir_gestao()
        except Exception as e:
            st.error(f"Erro na Gestão: {e}")

    elif escolha == "🚪 Sair":
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    executar()
