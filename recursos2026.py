import streamlit as st
import pandas as pd
import gdown
import os

# ... (Mantenha o dicionário ESTADO_PARA_SIGLA e a função limpar_valor iguais) ...

def exibir_recursos():
    # --- RECUPERAÇÃO DO USUÁRIO LOGADO ---
    # Aqui garantimos que o nome apareça conforme o cadastro
    usuario = st.session_state.get('usuario_logado', {})
    
    # Tenta pegar 'NOME', se não existir tenta 'USUARIO', se não, fica 'CONSULTOR'
    nome_exibicao = usuario.get('NOME') or usuario.get('USUARIO') or "CONSULTOR"
    
    st.title("📊 Radar de Recursos 2026")
    
    # ... (Lógica de download do arquivo e IDs do Drive) ...

    # --- SIDEBAR (MENU DA ESQUERDA CORRIGIDO) ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        # Alterado conforme sua solicitação para mostrar o usuário logado real
        st.info(f"**LOGIN:** {str(nome_exibicao).upper()}")
        
        # ... (Restante da lógica de Plano Básico/Premium) ...

    # ... (Restante do código de processamento da planilha e filtros) ...
