import streamlit as st
import pandas as pd
import gdown
import os

def exibir_recursos():
    st.title("🔍 Diagnóstico de Colunas - Radar 2026")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando arquivo para análise..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    try:
        # Lemos apenas as primeiras 5 linhas para ser instantâneo
        df_teste = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', nrows=5)
        
        st.write("### ✅ Arquivo lido com sucesso!")
        st.write("Abaixo estão os nomes exatos das colunas encontradas na sua base de dados:")
        
        # Exibe a lista de colunas para você me copiar e mandar
        colunas = list(df_teste.columns)
        st.json(colunas) 

        st.write("---")
        st.write("### 📋 Prévia dos Dados (Primeiras linhas):")
        st.dataframe(df_teste.head(3))
        
        st.warning("👉 **Oseias:** Por favor, copie a lista de nomes que apareceu acima (no quadro preto) e cole aqui no chat para eu ajustar o filtro de UF e Localidade com perfeição.")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
