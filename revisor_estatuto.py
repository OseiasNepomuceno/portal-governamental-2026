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
    # Tentativa de usar o modelo mais atualizado
    # O nome 'models/gemini-1.5-flash' é o padrão oficial para 2026
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = f"""
        Você é um consultor jurídico sênior da CORE ESSENCE.
        Analise o Estatuto Social abaixo e forneça um parecer técnico:
        
        1. Verifique conformidade com a Lei 13.019/2014 (MROSC).
        2. Identifique pontos de atenção na governança.
        3. Liste cláusulas faltantes ou ambíguas.

        Formate com Emojis:
        ✅ Pontos Positivos
        ⚠️ Atenção
        ❌ Faltantes
        💡 Sugestões

        Texto:
        {texto_estatuto[:30000]} 
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Se o 1.5-flash falhar, tentamos o gemini-pro como alternativa de segurança
        st.warning("Tentando modelo de backup...")
        model_backup = genai.GenerativeModel('gemini-pro')
        response = model_backup.generate_content(prompt)
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
