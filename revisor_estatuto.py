import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import io

# --- CONFIGURAÇÃO DA API ---
# Substitua pela sua chave real do Google AI Studio
API_KEY = "SUA_CHAVE_AQUI" 
genai.configure(api_key=API_KEY)

# 1. FUNÇÃO PARA EXTRAIR TEXTO (O que estava faltando!)
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

# 2. FUNÇÃO PARA ANALISAR COM O GEMINI
def analisar_estatuto(texto_estatuto):
    try:
        # Usando a versão estável mais recente para evitar erro 404
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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

# --- 3. INTERFACE DO USUÁRIO ---
st.title("📑 Revisor de Estatuto Inteligente")
st.caption("CORE ESSENCE - Inteligência Artificial Aplicada")
st.markdown("---")

st.write("### 📤 Upload do Documento")
arquivo = st.file_uploader("Arraste o PDF do Estatuto aqui", type=["pdf"])

if arquivo is not None:
    # O arquivo só é processado se for carregado
    with st.spinner("Extraindo texto do documento..."):
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
                    
                    # Botão para baixar o parecer em texto
                    st.download_button(
                        label="📥 Baixar Parecer em TXT",
                        data=resultado,
                        file_name="Parecer_Estatuto_CoreEssence.txt",
                        mime="text/plain"
                    )
    else:
        st.warning("Não foi possível extrair texto deste PDF. Verifique se ele não é apenas uma imagem.")

else:
    st.info("Aguardando upload de arquivo PDF para iniciar a revisão.")
