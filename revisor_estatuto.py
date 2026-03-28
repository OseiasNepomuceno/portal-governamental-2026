import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import io

# --- CONFIGURAÇÃO DA API ---
# DICA: Em produção, o ideal é usar st.secrets para esconder sua chave
API_KEY = "AIzaSyCkevsDNpmeFE3rB5y32Qm6jh5vxoi_ckg" 
genai.configure(api_key=API_KEY)

def extrair_texto_pdf(arquivo_pdf):
    leitor = PdfReader(arquivo_pdf)
    texto = ""
    for pagina in leitor.pages:
        texto += pagina.extract_text()
    return texto

def analisar_estatuto(texto_estatuto):
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Você é um consultor jurídico sênior especializado em Terceiro Setor e Gestão Governamental da consultoria CORE ESSENCE.
    Sua tarefa é revisar o Estatuto Social abaixo e fornecer um parecer técnico detalhado.
    
    Analise os seguintes pontos:
    1. Conformidade com o Código Civil.
    2. Presença de cláusulas obrigatórias para parcerias públicas (MROSC - Lei 13.019/2014).
    3. Clareza nos objetivos sociais e governança.
    4. Identificação de possíveis riscos jurídicos ou lacunas.

    Formate a resposta com:
    - ✅ Pontos Positivos
    - ⚠️ Pontos de Atenção (Necessário ajustar)
    - ❌ Cláusulas Faltantes
    - 💡 Sugestão de Redação Melhorada

    Texto do Estatuto:
    {texto_estatuto[:15000]} # Limitando caracteres para segurança do prompt
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- INTERFACE ---
st.title("📑 Revisor de Estatuto Inteligente")
st.caption("CORE ESSENCE - Inteligência Artificial Aplicada")
st.markdown("---")

st.write("### 📤 Upload do Documento")
arquivo = st.file_uploader("Arraste o PDF do Estatuto aqui", type=["pdf"])

if arquivo is not None:
    with st.spinner("Lendo documento..."):
        texto_extraido = extrair_texto_pdf(arquivo)
        st.success("Texto extraído com sucesso!")
        
    if st.button("Iniciar Análise com IA"):
        with st.spinner("O Gemini está analisando as cláusulas..."):
            try:
                resultado = analisar_estatuto(texto_extraido)
                st.markdown("---")
                st.subheader("📋 Parecer Técnico CORE ESSENCE")
                st.write(resultado)
                
                # Opção para baixar o parecer
                st.download_button(
                    label="📥 Baixar Parecer",
                    data=resultado,
                    file_name="Parecer_Tecnico_Estatuto.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Erro na análise: {e}")

else:
    st.info("Aguardando upload de arquivo PDF para iniciar a revisão.")
