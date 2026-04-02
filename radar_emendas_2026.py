import streamlit as st
import pandas as pd
import gdown
import os

# --- CONFIGURAÇÕES DE DADOS ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO"
}

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id: 
        return None, f"Chave {id_secret} não configurada."
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        # Separador ';' conforme seu Bloco de Notas
        df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, f"Erro na leitura: {e}"

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def limpar_valor_monetario(v):
    if pd.isna(v) or v is None: return 0.0
    v = str(v).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(v)
    except:
        return 0.0

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    # --- 1. RECUPERAÇÃO DE DADOS DO USUÁRIO ---
    plano_user = str(st.session_state.get('usuario_plano', 'BRONZE')).upper()
    usuario_info = st.session_state.get('usuario_logado', {})
    local_liberado = str(usuario_info.get('local_liberado', '')).upper().strip()

    # --- 2. PAINEL INFORMATIVO NO MENU LATERAL ---
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**Nível de Acesso:** `{plano_user}`")
        if local_liberado and local_liberado != "NAN":
            label_local = "Estado" if "PRATA" in plano_user else "Município(s)"
            st.info(f"📍 **{label_local} Liberado:**\n{local_liberado}")
        st.markdown("---")

    # --- 3. FILTROS DE INTERFACE ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos"

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados CORE ESSENCE..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        C_UF = "UF"
        C_MUN = "MUNICÍPIO"
        C_ANO = "ANO DA EMENDA"
        C_VAL
