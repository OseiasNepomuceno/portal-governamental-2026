import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

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
            if conteudo: texto += conteudo
        return texto
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return ""

# 2. FUNÇÃO DE ANÁLISE COM GEMINI
def analisar_estatuto(texto_estatuto):
    try:
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_escolhido = next((m for m in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro'] if m in modelos_disponiveis), modelos_disponiveis[0])
        model = genai.GenerativeModel(modelo_escolhido)
        
        prompt = f"""
        Você é o Consultor Sênior da CORE ESSENCE. Analise o estatuto abaixo com base no MROSC e na Portaria 33/2023.
        O parecer deve ser profissional, direto e estruturado para um documento oficial.
        
        Estruture em:
        1. ✅ PONTOS DE CONFORMIDADE
        2. ⚠️ GARGALOS E RISCOS (Base Portaria 33/2023)
        3. ❌ OMISSÕES OBRIGATÓRIAS
        4. 💡 RECOMENDAÇÃO CORE ESSENCE

        Ao final, adicione o campo:
        [NOME DO CONSULTOR]
        Consultor Sênior - CORE ESSENCE

        Texto: {texto_estatuto[:25000]}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Erro na IA: {e}")
        return None

# 3. FUNÇÃO PARA GERAR O ARQUIVO WORD (.DOCX)
def gerar_word_parecer(texto_parecer):
    doc = Document()
    
    # Cabeçalho
    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run("PARECER TÉCNICO DE CONFORMIDADE ESTATUTÁRIA")
    run.bold = True
    run.font.size = Pt(14)
    
    subtitulo = doc.add_paragraph()
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = subtitulo.add_run("CORE ESSENCE - Consultoria e Estratégia Governamental")
    run_sub.font.size = Pt(11)
    run_sub.italic = True

    doc.add_paragraph("_" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Corpo do texto
    # Removemos os asteriscos do Markdown para o Word ficar limpo
    texto_limpo = texto_parecer.replace("**", "")
    
    for linha in texto_limpo.split('\n'):
        p = doc.add_paragraph(linha)
        p.style.font.name = 'Arial'
        p.style.font.size = Pt(11)

    # Rodapé
    doc.add_paragraph("\n")
    footer = doc.add_paragraph("Documento gerado para revisão e edição técnica.")
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFACE STREAMLIT ---
st.title("📑 Revisor de Estatuto 33/2023")
st.caption("CORE ESSENCE - Inteligência Estratégica")

st.info("💡 **Diferencial:** Analisando conforme a nova **Portaria Conjunta 33/2023**. O arquivo final será baixado em **Word** para sua edição.")

arquivo = st.file_uploader("Upload do Estatuto (PDF)", type=["pdf"])

if arquivo:
    texto_extraido = extrair_texto_pdf(arquivo)
    if texto_extraido:
        st.success("Documento carregado!")
        if st.button("🚀 Gerar Minuta de Parecer (Word)"):
            with st.spinner("Analisando e formatando documento editável..."):
                resultado = analisar_estatuto(texto_extraido)
                if resultado:
                    st.markdown("---")
                    st.subheader("📋 Prévia da Análise")
                    st.write(resultado)
                    
                    word_final = gerar_word_parecer(resultado)
                    
                    st.download_button(
                        label="📥 Baixar Parecer Editável (.docx)",
                        data=word_final,
                        file_name="Parecer_CoreEssence_Editavel.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
