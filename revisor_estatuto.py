import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import io

def exibir_revisor():
    # --- 1. CAPTURA DADOS DO LOGIN JÁ EXISTENTE ---
    # O sistema de login que você fez já salva o 'usuario_logado'
    usuario = st.session_state.get('usuario_logado', {})
    
    if not usuario:
        st.warning("⚠️ Por favor, realize o login para acessar o revisor.")
        return

    email = usuario.get('usuario', 'Consultor')
    plano = str(usuario.get('PLANO', 'BASICO')).upper()
    
    # Definindo limites baseados no seu modelo de negócio
    limite = 150 if plano == "PREMIUM" else 50

    # Recupera o contador que já deve estar na planilha ou na sessão
    # Se você já criou a coluna REVISOES_USADAS na planilha de licenças:
    uso_atual = usuario.get('REVISOES_USADAS', 0)

    # --- INTERFACE ---
    col_t, col_st = st.columns([3, 1])
    with col_t:
        st.header("📜 Revisor de Estatuto 33/2023")
    with col_st:
        # Mostra o medidor de progresso/uso
        st.metric("Saldo de Revisões", f"{uso_atual}/{limite}")

    # --- 2. TRAVA DE SEGURANÇA ---
    if uso_atual >= limite:
        st.error(f"🚫 Limite atingido para o Plano {plano}.")
        st.info("Para liberar mais revisões, entre em contato com a administração da Core Essence.")
        return

    # --- 3. LÓGICA DE REVISÃO ---
    arquivo = st.file_uploader("Faça o upload do Estatuto em PDF", type=["pdf"])
    
    if arquivo:
        # Extração e Botão de Análise
        if st.button("🚀 Iniciar Análise Estratégica"):
            with st.spinner("O Consultor IA está analisando..."):
                # Aqui você chama a sua função de análise do Gemini
                # ... (lógica de extração e API Gemini) ...
                
                # SUCESSO NA ANÁLISE:
                # Importante: Para persistir na planilha, você precisa dar um 
                # update no dataframe original que foi carregado no login.
                
                uso_atual += 1
                st.session_state.usuario_logado['REVISOES_USADAS'] = uso_atual
                
                st.success(f"✅ Revisão concluída! Novo saldo: {uso_atual}/{limite}")
                
                # Se o seu sistema tiver uma função 'salvar_dados()', chame-a aqui
                # para enviar o novo valor de volta ao Google Drive.
                
                st.rerun()

    st.markdown("---")
    st.caption(f"Logado como: {email} | Core Essence © 2026")
