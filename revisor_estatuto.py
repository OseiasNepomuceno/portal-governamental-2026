import streamlit as st
import fitz  # PyMuPDF
from docx import Document
import google.generativeai as genai
from openai import OpenAI
from io import BytesIO

# --- CONFIGURAÇÕES DE CHAVES ---
CHAVE_GEMINI = "AIzaSyBLAyEfqwLz8GqV8QYYEMhXJSQxCIjUv4A"
CHAVE_OPENAI = "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"

# Inicialização dos Clientes
genai.configure(api_key=CHAVE_GEMINI)
client_gpt = OpenAI(api_key=CHAVE_OPENAI)


# --- MOTORES DE INTELIGÊNCIA ---

def revisar_com_gemini(prompt):
    """Tenta processar com a IA do Google"""
    # Testamos múltiplos nomes de modelo para evitar o erro 404
    for modelo_nome in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']:
        try:
            model = genai.GenerativeModel(modelo_nome)
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            continue
    raise Exception("Falha em todas as versões do Gemini")


def revisar_com_chatgpt(prompt):
    """Tenta processar com a IA da OpenAI"""
    response = client_gpt.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um consultor jurídico especialista em Transferegov."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


# --- FUNÇÕES DE SUPORTE ---

def extrair_texto_pdf(arquivo_pdf):
    documento = fitz.open(stream=arquivo_pdf.read(), filetype="pdf")
    return "".join([pagina.get_text() for pagina in documento])


def criar_docx(texto):
    doc = Document()
    doc.add_heading('Estatuto Social Revisado - Consultoria IA', 0)
    for p in texto.split('\n'):
        if p.strip(): doc.add_paragraph(p.strip())
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# --- INTERFACE ---
st.set_page_config(page_title="Revisor Híbrido Pro", layout="wide")
st.title("⚖️ Revisor de Estatutos Transferegov")

with st.sidebar:
    st.header("Configurações")
    modo_ia = st.radio("Prioridade de Processamento:", ["Híbrido (Auto)", "Somente Gemini", "Somente ChatGPT"])
    diretriz = st.selectbox("Portaria de Referência:",
                            ["Portaria 134/2023", "MROSC 13.019/2014", "Decreto 11.531/2023"])

upload = st.file_uploader("Suba o Estatuto em PDF", type="pdf")

if st.button("🚀 Iniciar Revisão Inteligente") and upload:
    texto_bruto = extrair_texto_pdf(upload)
    prompt_final = f"Revise este estatuto: {texto_bruto} seguindo as regras da {diretriz}. Retorne o texto completo."

    resultado = None
    metodo_usado = ""

    with st.spinner("Analisando cláusulas..."):
        # Lógica Híbrida
        if modo_ia in ["Híbrido (Auto)", "Somente Gemini"]:
            try:
                resultado = revisar_com_gemini(prompt_final)
                metodo_usado = "Google Gemini (Principal)"
            except Exception as e:
                if modo_ia == "Somente Gemini":
                    st.error(f"Erro no Gemini: {e}")
                else:
                    st.warning("Gemini indisponível. Acionando ChatGPT de emergência...")

        if resultado is None and modo_ia in ["Híbrido (Auto)", "Somente ChatGPT"]:
            try:
                resultado = revisar_com_chatgpt(prompt_final)
                metodo_usado = "OpenAI ChatGPT (Backup/Manual)"
            except Exception as e:
                st.error(f"Falha total nos sistemas de IA: {e}")

    if resultado:
        st.success(f"Sucesso! Processado via: {metodo_usado}")
        st.text_area("Resultado da Revisão", resultado, height=400)
        st.download_button("📥 Baixar Documento Editável", criar_docx(resultado), "estatuto_revisado.docx")