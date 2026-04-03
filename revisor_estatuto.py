import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import io

def exibir_revisor():
    # --- 1. CAPTURA DADOS DO LOGIN JÁ EXISTENTE ---
    usuario = st.session_state.get('usuario_logado', {})
    
    if not usuario:
        st.warning("⚠️ Por favor, realize o login para acessar o revisor.")
        return

    email = usuario.get('USUARIO', 'Consultor') # Ajustado para bater com a chave em maiúsculo
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper().strip()
    
    # --- ATUALIZAÇÃO DOS LIMITES ESTRATÉGICOS ---
    # Aceita 'BÁSICO' ou 'BASICO' para evitar erros de acentuação na planilha
    if plano == "PREMIUM":
        limite = 15
    else:
        limite = 10

    # Recupera o contador de revisões usadas
    uso_atual = usuario.get('REVISOES_USADAS', 0)

    # --- INTERFACE ---
    col_t, col_st = st.columns([3, 1])
    with col_t:
        st.header("📜 Revisor de Estatuto 33/2023")
    with col_st:
        # Mostra o medidor de progresso/uso atualizado
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
                # --- ESPAÇO PARA CHAMADA DA API GEMINI ---
                # (Aqui entra sua lógica de extração de texto e prompt)
                # -----------------------------------------
                
                # SIMULAÇÃO DE SUCESSO NA ANÁLISE:
                uso_atual += 1
                
                # Atualiza o estado da sessão para refletir no portal principal imediatamente
                st.session_state.usuario_logado['REVISOES_USADAS'] = uso_atual
                
                st.success(f"✅ Revisão concluída! Novo saldo: {uso_atual}/{limite}")
                
                # DICA: Para que esse número persista no Google Sheets, você precisará
                # criar uma função para dar 'update' na célula da planilha 'usuario'.
                
                st.rerun()

    st.markdown("---")
    st.caption(f"Logado como: {email} | Core Essence © 2026")
