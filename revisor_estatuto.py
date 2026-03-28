import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# --- CONFIGURAÇÃO DA API (FORÇANDO VERSÃO ESTÁVEL) ---
API_KEY = "SUA_CHAVE_AQUI" 
genai.configure(api_key=API_KEY)

def analisar_estatuto(texto_estatuto):
    try:
        # Usando o nome técnico completo e atualizado para 2026
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        prompt = f"""
        Você é um consultor jurídico sênior da CORE ESSENCE especializado em MROSC (Lei 13.019/2014).
        Analise o Estatuto Social abaixo e forneça um parecer técnico rigoroso.
        
        Estruture sua resposta assim:
        1. ✅ PONTOS DE CONFORMIDADE: O que o estatuto já atende legalmente.
        2. ⚠️ PONTOS DE ATENÇÃO: Cláusulas ambíguas ou que geram risco.
        3. ❌ CLÁUSULAS FALTANTES: O que é obrigatório e não foi encontrado (ex: destinação de bens, ficha limpa, etc).
        4. 💡 RECOMENDAÇÃO CORE ESSENCE: Sugestão de redação para as correções.

        Texto do Estatuto:
        {texto_estatuto[:30000]} 
        """
        
        # Gerando o conteúdo
        response = model.generate_content(prompt)
        
        # Verificação de segurança para a resposta
        if response.text:
            return response.text
        else:
            return "A IA não conseguiu gerar uma resposta. Verifique o conteúdo do PDF."
            
    except Exception as e:
        # Log detalhado para te ajudar se ainda houver erro
        st.error(f"Detalhe técnico do erro: {e}")
        return None

# --- RESTANTE DA INTERFACE PERMANECE IGUAL ---
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
