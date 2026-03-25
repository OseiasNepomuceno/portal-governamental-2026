import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Radar de Emendas 2026", layout="wide")
st.title("🏛️ Radar de Emendas Parlamentares")


def carregar_dados(caminho):
    if not os.path.exists(caminho): return None
    df = pd.read_csv(caminho, sep=None, engine='python', encoding='latin1')
    df.columns = df.columns.str.strip().str.upper()
    return df


df = carregar_dados("emendas_parlamentares_2026.csv")

if df is not None:
    # --- COLUNAS EXATAS QUE VOCÊ ME PASSOU ---
    col_uf = "UF"
    col_autor = "NOME DO AUTOR DA EMENDA"
    col_valor = "VALOR EMPENHADO"
    col_mun = "MUNICÍPIO"

    # Limpeza de Moeda
    df[col_valor] = df[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)

    # Filtros
    st.sidebar.header("⚙️ Filtros")
    lista_uf = sorted(df[col_uf].unique().astype(str))
    uf_sel = st.sidebar.multiselect("Selecione o Estado:", lista_uf,
                                    default=["SP"] if "SP" in lista_uf else lista_uf[:1])

    df_uf = df[df[col_uf].isin(uf_sel)]
    lista_autores = sorted(df_uf[col_autor].unique())
    autor_sel = st.sidebar.multiselect("Filtrar Parlamentar:", lista_autores)

    # Aplicação dos Filtros
    mask = df[col_uf].isin(uf_sel)
    if autor_sel: mask = mask & (df[col_autor].isin(autor_sel))
    df_filtrado = df[mask].copy()

    # Dashboard
    c1, c2, c3 = st.columns(3)
    total = df_filtrado[col_valor].sum()
    c1.metric("Qtd. Emendas", len(df_filtrado))
    c2.metric("Total em Recursos", f"R$ {total:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
    c3.metric("Municípios Atendidos", df_filtrado[col_mun].nunique())

    # Gráfico
    st.markdown("### 📊 Top 10 Parlamentares por Valor em " + ", ".join(uf_sel))
    grafico = df_filtrado.groupby(col_autor)[col_valor].sum().sort_values(ascending=False).head(10)
    st.bar_chart(grafico)

    st.dataframe(df_filtrado[[col_uf, col_mun, col_autor, col_valor]], use_container_width=True)