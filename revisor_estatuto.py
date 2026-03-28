import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- CONFIGURAÇÃO DA API ---
API_KEY = "AIzaSyCkevsDNpmeFE3rB5y32Qm6jh5vxoi_ckg" 
genai.configure(api_key=API_KEY)

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

def analisar_estatuto(texto_estatuto):
    try:
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_escolhido = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro'] if m in modelos_disponiveis), modelos_disponiveis[0])

        model = genai.GenerativeModel(modelo_escolhido)
        
        # PROMPT ATUALIZADO COM FOCO NA PORTARIA 33/2023
        prompt = f"""
        Você é um consultor jurídico sênior da CORE ESSENCE, autoridade em parcerias governamentais.
        Sua revisão deve ser RIGOROSA e baseada na PORTARIA CONJUNTA MGI/MF/CGU Nº 33/2023 (que sucedeu a 424/2016) e no MROSC (Lei 13.019/2014).
        
        Analise o texto do Estatuto abaixo focando em:
        1. Cláusulas de governança e transparência exigidas pela Portaria 33/2023.
        2. Critérios de habilitação para celebração no Transferegov.
        3. Destinação de bens e ausência de impedimentos para dirigentes.
        4. Adequação dos objetivos sociais para captação de recursos federais.

        Estruture sua resposta com:
        ---
        📢 **NOTA DE CONSULTORIA:** Esta análise técnica foi realizada com base nas diretrizes da **Portaria Conjunta MGI/MF/CGU nº 33/2023**.
        ---
        ✅ **CONFORMIDADE LEGAL:** O que está correto.
        ⚠️ **GARGALOS E RISCOS:** Pontos que podem travar a captação na 33/2023.
        ❌ **OMISSÕES OBRIGATÓRIAS:** O que falta inserir urgentemente.
        💡 **REDAÇÃO SUGERIDA CORE ESSENCE:** Texto pronto para o novo estatuto.

        Texto:
        {texto_estatuto[:30000]} 
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Erro na comunicação com a IA: {e}")
        return None

# --- INTERFACE ---
st.title("📑 Revisor de Estatuto Inteligente")
st.caption("CORE ESSENCE - Consultoria e Estratégia Governamental")

# Ênfase visual no painel
st.info("💡 **Diferencial CORE ESSENCE:** Nossa IA está atualizada com a **Portaria 33/2023**, garantindo conformidade para captação no Transferegov.")
st.markdown("---")

arquivo = st.file_uploader("Arraste o PDF do Estatuto para análise", type=["pdf"])

if arquivo:
    texto_extraido = extrair_texto_pdf(arquivo)
    if texto_extraido:
        st.success("Documento carregado com sucesso!")
        if st.button("🚀 Iniciar Análise Estratégica"):
            with st.spinner("Analisando conformidade com a Portaria 33/2023..."):
                resultado = analisar_estatuto(texto_extraido)
                if resultado:
                    st.markdown("---")
                    st.subheader("📋 Parecer Técnico Final")
                    st.markdown(resultado)
                    st.download_button("📥 Baixar Parecer (.txt)", data=resultado, file_name="Parecer_Tecnico_33_2023.txt")
