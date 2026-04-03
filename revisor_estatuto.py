import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

def exibir_revisor():
    # --- 1. LÓGICA DE CONTROLE DE PLANOS (NOVO) ---
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BASICO')).upper()
    
    # Define o limite baseado no plano informado no login
    limite_revisoes = 150 if plano == "PREMIUM" else 50
    
    # Inicializa o contador na sessão se não existir
    if 'contador_revisoes' not in st.session_state:
        st.session_state.contador_revisoes = 0

    # --- CONFIGURAÇÃO DA API ---
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Erro: GEMINI_API_KEY não encontrada nos Secrets do Streamlit.")
        return

    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    
    # 2. FUNÇÕES AUXILIARES
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
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Você é o Consultor Sênior da CORE ESSENCE. Analise o estatuto abaixo com base no MROSC (Lei 13.019/2014) e na Portaria Conjunta 33/2023.
            Estruture a resposta exatamente assim:
            1. ✅ PONTOS DE CONFORMIDADE
            2. ⚠️ GARGALOS E RISCOS
            3. ❌ OMISSÕES OBRIGATÓRIAS
            4. 💡 RECOMENDAÇÃO CORE ESSENCE
            
            Texto do Estatuto: {texto_estatuto[:28000]}
            """
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Erro na IA: {e}")
            return None

    def gerar_word_parecer(texto_parecer):
        doc = Document()
        titulo = doc.add_paragraph()
        titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = titulo.add_run("PARECER TÉCNICO DE CONFORMIDADE ESTATUTÁRIA")
        run.bold = True
        run.font.size = Pt(14)
        
        texto_limpo = texto_parecer.replace("**", "").replace("###", "").replace("##", "")
        for linha in texto_limpo.split('\n'):
            if linha.strip():
                p = doc.add_paragraph(linha.strip())
                if p.runs: p.runs[0].font.name = 'Arial'
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    # --- INTERFACE ---
    st.header("📜 Revisor de Estatuto 33/2023")
    
    # Exibe contador na lateral
    st.sidebar.markdown(f"### 📊 Uso do Plano")
    st.sidebar.info(f"Plano: **{plano}**\n\nRevisões: **{st.session_state.contador_revisoes} / {limite_revisoes}**")
    
    # Bloqueio se atingir o limite
    if st.session_state.contador_revisoes >= limite_revisoes:
        st.error(f"🚫 Limite de revisões atingido para o plano {plano} ({limite_revisoes} revisões).")
        st.warning("Para continuar revisando, solicite um upgrade de plano.")
        return

    st.write("Análise de conformidade para OSCs e Entidades do Terceiro Setor.")
    arquivo = st.file_uploader("Faça o upload do Estatuto em PDF", type=["pdf"])
    
    if arquivo:
        texto_extraido = extrair_texto_pdf(arquivo)
        if texto_extraido:
            st.success("✅ Documento carregado!")
            
            if st.button("🚀 Iniciar Análise Estratégica"):
                with st.spinner("O Consultor IA está revisando as cláusulas..."):
                    resultado = analisar_estatuto(texto_extraido)
                    
                    if resultado:
                        # CONTABILIZA A REVISÃO APÓS O SUCESSO
                        st.session_state.contador_revisoes += 1
                        st.rerun() # Atualiza a tela para mostrar o novo saldo no sidebar

    # Se já houver um resultado na memória (pós-botão), exibe as opções de download
    # (Lógica simplificada para manter o fluxo do Streamlit)
