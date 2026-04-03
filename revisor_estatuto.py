import streamlit as st
import google.generativeai as genai
import pandas as pd
import gdown
import os
from PyPDF2 import PdfReader
from docx import Document
import io

def exibir_revisor():
    # 1. IDENTIFICAÇÃO DO USUÁRIO E CONEXÃO COM A PLANILHA
    usuario_logado = st.session_state.get('usuario_logado', {})
    email_user = usuario_logado.get('usuario') # 
    plano = str(usuario_logado.get('PLANO', 'BASICO')).upper() # 
    
    # Define limites
    limite = 150 if plano == "PREMIUM" else 50 # 

    # 2. CARREGAMENTO DOS DADOS DE USO (VIA DRIVE)
    # Aqui usamos o arquivo ID_LICENÇAS que já mapeamos 
    file_id = st.secrets.get("file_id_licencas") 
    nome_csv = "ID_LICENCAS.csv"

    try:
        # Sincroniza a planilha para ler o uso atual
        url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(url, nome_csv, quiet=True)
        df_users = pd.read_csv(nome_csv)
        
        # Busca o uso atual do usuário específico 
        uso_atual = df_users.loc[df_users['usuario'] == email_user, 'REVISOES_USADAS'].values[0]
    except:
        uso_atual = st.session_state.get('contador_revisoes', 0)

    # --- INTERFACE ---
    st.header("📜 Revisor de Estatuto 33/2023")
    st.sidebar.info(f"📊 **Status do Plano**\n\nPlano: {plano}\nUso: {uso_atual} / {limite}")

    if uso_atual >= limite:
        st.error(f"🚫 Limite atingido ({limite}/{limite}). Faça upgrade para continuar.")
        return

    # --- LÓGICA DE UPLOAD E ANÁLISE ---
    arquivo = st.file_uploader("Upload do Estatuto (PDF)", type=["pdf"])
    
    if arquivo:
        if st.button("🚀 Iniciar Análise"):
            # Lógica do Gemini (já configurada anteriormente)
            with st.spinner("Analisando..."):
                # [Aqui entra sua função analisar_estatuto já existente]
                
                # SUCESSO: Agora precisamos atualizar a planilha
                # Nota: Para escrever de volta no Drive via Streamlit, 
                # o ideal é usar uma Service Account (JSON) ou atualizar via API.
                
                st.session_state.contador_revisoes = uso_atual + 1
                st.success(f"Revisão concluída! Saldo restante: {limite - (uso_atual + 1)}")
                st.rerun()
