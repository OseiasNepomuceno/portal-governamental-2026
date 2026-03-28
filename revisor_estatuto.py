import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- CONFIGURAÇÃO DA API ---
API_KEY = "AIzaSyCkevsDNpmeFE3rB5y32Qm6jh5vxoi_ckg" 
genai.configure(api_key=API_KEY)

# 1. FUNÇÃO PARA EXTRAIR TEXTO
def extrair_texto_pdf(arquivo_pdf):
    try:
        leitor = PdfReader(arquivo_pdf)
        texto = ""
        for pagina in leitor.pages:
            conteudo = pagina.extract_text()
            if conteudo:
                texto += conteudo
        return texto
    except Exception as e:
        st.error(f"Erro ao ler o arquivo PDF: {e}")
        return ""

# 2. FUNÇÃO DE ANÁLISE COM VARREDURA DE MODELO (CORREÇÃO DO ERRO 404)
def analisar_estatuto(texto_estatuto):
    try:
        # Lista os modelos disponíveis para a sua chave API
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ordem de preferência: Flash 1.5 (mais rápido) -> Pro 1.5 -> Pro 1.0 (antigo)
        if 'models/gemini-1.5-flash' in modelos_disponiveis:
            modelo_escolhido = 'models/gemini-1.5-flash'
        elif 'models/gemini-1.5-pro' in modelos_disponiveis:
            modelo_escolhido = 'models/gemini-1.5-pro'
        elif 'models/gemini-pro' in modelos_disponiveis:
            modelo_escolhido = 'models/gemini-pro'
        else:
            # Pega o primeiro disponível se nenhum dos acima for encontrado
            modelo_escolhido = modelos_disponiveis[0] if modelos_disponiveis else None

        if not modelo_escolhido:
            st.error("Nenhum modelo compatível encontrado na sua conta Google.")
            return None

        st.info(f"Usando modelo: {modelo_escolhido}")
        model = genai.GenerativeModel(modelo_escolhido)
        
        prompt = f"""
        Você é um consultor jurídico sênior da CORE ESSENCE especializado em MROSC (Lei 13.019/2014).
        Analise o Estatuto Social abaixo e forneça um parecer técnico rigoroso.
        
        Estruture sua resposta com estes tópicos:
        1. ✅ PONTOS DE CONFORMIDADE: O que o estatuto já atende legalmente.
        2. ⚠️ PONTOS DE ATENÇÃO: Cláusulas ambíguas ou que geram risco.
        3. ❌ CLÁUSULAS FALTANTES: O que é obrigatório e não foi encontrado.
        4. 💡 RECOMENDAÇÃO CORE ESSENCE: Sugestão de redação para as correções.

        Texto do Estatuto:
        {texto_estatuto[:30000]} 
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Erro na comunicação com a IA: {e}")
        return None

# --- INTERFACE ---
st.title("📑 Revisor de Estatuto Inteligente")
st.caption("CORE ESSENCE - Inteligência Artificial Aplicada")
st.markdown("---")

arquivo = st.file_uploader("Arraste o PDF do Estatuto aqui", type=["pdf"])

if arquivo:
    texto_extraido = extrair_texto_pdf(arquivo)
    if texto_extraido:
        st.success("Texto extraído com sucesso!")
        if st.button("Iniciar Análise CORE ESSENCE"):
            with st.spinner("O Gemini está analisando as cláusulas..."):
                resultado = analisar_estatuto(texto_extraido)
                if resultado:
                    st.markdown("---")
                    st.subheader("📋 Parecer Técnico")
                    st.markdown(resultado)
                    st.download_button("📥 Baixar Parecer", data=resultado, file_name="Parecer_Estatuto.txt")
