import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
import io
import os

# --- CONFIGURAÇÃO DA API ---
API_KEY = "AIzaSyCkevsDNpmeFE3rB5y32Qm6jh5vxoi_ckg" 
genai.configure(api_key=API_KEY)

# --- FUNÇÕES TÉCNICAS ---
def extrair_texto_pdf(arquivo_pdf):
    try:
        leitor = PdfReader(arquivo_pdf)
        texto = ""
        for pagina in leitor.pages:
            conteudo = pagina.extract_text()
            if conteudo: texto += conteudo
        return texto
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return ""

def analisar_estatuto(texto_estatuto):
    try:
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_escolhido = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro'] if m in modelos_disponiveis), modelos_disponiveis[0])
        model = genai.GenerativeModel(modelo_escolhido)
        
        prompt = f"""
        Você é o Consultor Sênior da CORE ESSENCE. Analise o estatuto abaixo com base no MROSC e na Portaria 33/2023.
        O parecer deve ser profissional, direto e dividido em:
        1. ✅ PONTOS DE CONFORMIDADE
        2. ⚠️ GARGALOS E RISCOS (Base 33/2023)
        3. ❌ OMISSÕES OBRIGATÓRIAS
        4. 💡 RECOMENDAÇÃO CORE ESSENCE

        Texto: {texto_estatuto[:25000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Erro na IA: {e}")
        return None

def gerar_pdf_parecer(texto_parecer):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    # --- CABEÇALHO ---
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=100, height=50)
        logo.hAlign = 'LEFT'
        elementos.append(logo)
    
    elementos.append(Paragraph("<font size=18 color='#1D3557'><b>CORE ESSENCE - Consultoria Governamental</b></font>", styles['Title']))
    elementos.append(Paragraph("<font size=10 color='gray'>Parecer Técnico de Conformidade Estatutária - Base: Portaria 33/2023</font>", styles['Normal']))
    elementos.append(Spacer(1, 20))
    
    # --- CONTEÚDO ---
    # Limpeza básica de caracteres que podem quebrar o PDF
    texto_formatado = texto_parecer.replace("\n", "<br/>").replace("**", "<b>").replace("*", "•")
    
    style_corpo = styles["Normal"]
    style_corpo.fontSize = 11
    style_corpo.leading = 14
    
    elementos.append(Paragraph(texto_formatado, style_corpo))
    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph("<hr/>", styles['Normal']))
    elementos.append(Paragraph("<font size=9 color='gray'>Documento gerado automaticamente pelo Sistema CORE ESSENCE em 2026.</font>", styles['Normal']))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# --- INTERFACE STREAMLIT ---
st.title("📑 Revisor de Estatuto 33/2023")
st.caption("CORE ESSENCE - Inteligência Estratégica")

st.info("💡 **Destaque:** Analisando conforme a nova **Portaria Conjunta 33/2023**.")

arquivo = st.file_uploader("Upload do Estatuto (PDF)", type=["pdf"])

if arquivo:
    texto_extraido = extrair_texto_pdf(arquivo)
    if texto_extraido:
        st.success("Documento pronto para análise.")
        if st.button("🚀 Gerar Parecer Oficial"):
            with st.spinner("Analisando cláusulas e gerando PDF..."):
                resultado = analisar_estatuto(texto_extraido)
                if resultado:
                    st.markdown("---")
                    st.subheader("📋 Visualização do Parecer")
                    st.write(resultado)
                    
                    # Gerar e disponibilizar PDF
                    pdf_final = gerar_pdf_parecer(resultado)
                    
                    st.download_button(
                        label="📥 Baixar Parecer em PDF Timbrado",
                        data=pdf_final,
                        file_name="Parecer_Tecnico_CoreEssence.pdf",
                        mime="application/pdf"
                    )
