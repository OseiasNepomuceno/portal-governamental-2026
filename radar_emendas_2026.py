import streamlit as st
import pandas as pd
import gdown
import os

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares 2026")

    # ... (Sua lógica de IDs e download do arquivo permanece igual) ...
    file_id = st.secrets.get("file_id_emendas")
    nome_arquivo = "2026_Emendas.csv"

    # --- CORREÇÃO DO ERRO DE LEITURA ---
    try:
        # Removido 'low_memory' e garantido o engine='python' com encoding correto
        df = pd.read_csv(
            nome_arquivo, 
            sep=None, 
            engine='python', 
            encoding='latin1', 
            on_bad_lines='skip'
        )
        
        # Padroniza colunas para evitar erros de busca
        df.columns = [str(c).upper().strip() for c in df.columns]

    except Exception as e:
        st.error(f"Não foi possível carregar a base: Erro na leitura: {e}")
        return

    # --- FILTRO POR ESTADO (MESMA LÓGICA DO RECURSOS 2026) ---
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    local_cadastrado = str(usuario.get('LOCALIDADE') or "RJ").strip().upper()
    
    # Se não for Premium/Diamante, filtra pela UF do consultor
    if plano not in ["PREMIUM", "DIAMANTE", "OURO"] and "UF" in df.columns:
        df = df[df["UF"].astype(str).str.strip().upper() == local_cadastrado]

    # ... (Restante do seu código de exibição da tabela) ...
    st.dataframe(df, use_container_width=True, hide_index=True)
