import gdown
import pandas as pd
import streamlit as st

# COLOQUE O ID REAL DA SUA PLANILHA AQUI (o que você pegou no Drive)
id_da_planilha = '1p_ihzkzi-osypEKjOaBy8LKz5rR9Kqtc' 
url = f'https://drive.google.com/uc?id={id_da_planilha}'
output = 'base_dados.xlsx'

try:
    # O parâmetro fuzzy=True ajuda muito se o link tiver caracteres extras
    gdown.download(url, output, quiet=False, fuzzy=True)
    df = pd.read_excel(output)
    st.success("Dados do Radar carregados!")
    # ... resto do seu código de filtros e gráficos ...
except Exception as e:
    st.error(f"Erro ao processar base de dados: {e}")
