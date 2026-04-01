import streamlit as st
import pandas as pd
import gdown
import os
import importlib

# --- CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA LINHA DE UI) ---
st.set_page_config(
    page_title="Core Essence - Portal de Gestão",
    page_icon="🛰️",
    layout="wide"
)

# --- FUNÇÃO DE LOGIN E PLANOS ---
def validar_usuario_plano():
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas_temp.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        # Buscando dados do Oseias (ajuste conforme seu login real)
        dados = df[df['usuario'].str.lower() == "oseias"].iloc[0]
        
        st.session_state['usuario_nome'] = dados['usuario']
        st.session_state['usuario_plano'] = str(dados['plano']).upper()
        st.session_state['usuario_status'] = str(dados['status']).lower()
    except:
        # Fallback de segurança para não travar o portal
        st.session_state['usuario_nome'] = "Oseias"
        st.session_state['usuario_plano'] = "BRONZE"
        st.session_state['usuario_status'] = "ativo"

def executar():
    # Inicializa os dados do plano se necessário
    if 'usuario_plano' not in st.session_state:
        validar_usuario_plano()

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("Painel de Controle")
        
        # Tag Visual do Plano
        plano = st.session_state.get('usuario_plano', 'BRONZE')
        st.info(f"🏆 Plano Atual: {plano}")
        
        st.markdown("---")
        menu_opcoes = ["📊 Recursos", "🏛️ Radar de Emendas", "📜 Revisão de Estatuto", "⚙️ Gestão Administrativa", "🚪 Sair"]
        escolha = st.radio("Selecione o Módulo:", menu_opcoes)
        
        st.markdown("---")
        st.caption(f"Logado como: {st.session_state.get('usuario_nome')}")

    # --- LÓGICA DE NAVEGAÇÃO (TODOS OS ELIF ALINHADOS) ---
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
        st.info(f"Seu plano {plano} permite {limite} revisões.")
        
        arquivo = st.file_uploader("Carregar documento (PDF)", type=["pdf"])
        if arquivo:
            st.success("Documento carregado! Inicie a análise profissional.")

    elif "Gestão" in escolha:
        try:
            import gestao as adm
            importlib.reload(adm)
            adm.exibir_gestao()
        except Exception as e:
            st.error(f"Erro no módulo Gestão: {e}")

    elif escolha == "🚪 Sair":
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.title("Sessão Encerrada")
        st.success("Saída efetuada com sucesso.")
        if st.button("Reiniciar Portal"):
            st.rerun()
        st.stop()

if __name__ == "__main__":
    executar()
