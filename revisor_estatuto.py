import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import io
import gspread
from google.oauth2.service_account import Credentials

# --- FUNÇÃO DE ATUALIZAÇÃO PERMANENTE (COLUNA 6 - F) ---
def atualizar_uso_revisor_gsheets(email_usuario, novo_valor):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        # Certifique-se de que o arquivo .json da sua conta de serviço está na mesma pasta
        nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
        creds = Credentials.from_service_account_file(nome_da_chave, scopes=scope)
        client = gspread.authorize(creds)
        planilha = client.open("ID_LICENÇAS").worksheet("usuario")
        
        # Localiza o usuário pelo e-mail na planilha
        celula = planilha.find(email_usuario)
        
        # ATUALIZAÇÃO: Ajustado para a Coluna 6 (Coluna F) conforme sua solicitação
        planilha.update_cell(celula.row, 6, novo_valor)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")
        return False

def exibir_revisor():
    # --- 1. CAPTURA DADOS DO LOGIN ---
    usuario = st.session_state.get('usuario_logado', {})
    
    if not usuario:
        st.warning("⚠️ Por favor, realize o login para acessar o revisor.")
        return

    # Dados do usuário vindos da sessão
    email = usuario.get('USUARIO', 'Consultor') 
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper().strip()
    
    # --- DEFINIÇÃO DINÂMICA DE LIMITES ---
    if plano == "PREMIUM":
        limite = 15
    else:
        limite = 10

    # Pega o uso atual (já carregado do Sheets no momento do login)
    uso_atual = usuario.get('REVISOES_USADAS', 0)

    # --- INTERFACE DO MÓDULO ---
    col_t, col_st = st.columns([3, 1])
    with col_t:
        st.header("📜 Revisor de Estatuto 33/2023")
    with col_st:
        # Exibe o contador visual 10/10 ou 15/15
        st.metric("Saldo de Revisões", f"{uso_atual}/{limite}")

    # --- 2. TRAVA DE SEGURANÇA (BLOQUEIA UPLOAD SE LIMITE ATINGIDO) ---
    if uso_atual >= limite:
        st.error(f"🚫 Limite de {limite} revisões atingido para o Plano {plano}.")
        st.info("Para liberar novos créditos, entre em contato com o suporte da Core Essence.")
        return

    # --- 3. ÁREA DE UPLOAD E ANÁLISE ---
    arquivo = st.file_uploader("Selecione o arquivo do Estatuto (PDF)", type=["pdf"])
    
    if arquivo:
        if st.button("🚀 Iniciar Análise Estratégica"):
            with st.spinner("O Consultor IA está processando os dados e salvando seu saldo..."):
                
                # --- AQUI VOCÊ DEVE INSERIR SUA LÓGICA DO GEMINI NO FUTURO ---
                # Exemplo: texto = extrair_texto_pdf(arquivo) -> resposta = chamar_gemini(texto)
                # -----------------------------------------------------------
                
                # Cálculo do novo total
                novo_total = uso_atual + 1
                
                # EXECUÇÃO DA GRAVAÇÃO NO GOOGLE SHEETS
                if atualizar_uso_revisor_gsheets(email, novo_total):
                    # Se gravou no Sheets, atualizamos a memória local (Session State)
                    st.session_state.usuario_logado['REVISOES_USADAS'] = novo_total
                    
                    st.success(f"✅ Análise concluída com sucesso! Novo saldo: {novo_total}/{limite}")
                    
                    # Reroda o app para atualizar o contador na Home e no Sidebar
                    st.rerun()
                else:
                    st.error("❌ Falha técnica ao salvar seu saldo. A análise foi cancelada para não gerar erro de contagem.")

    st.markdown("---")
    st.caption(f"Logado como: {email} | Core Essence © 2026")
