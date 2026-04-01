import streamlit as st
import pandas as pd
import gdown
import os

# --- IDs DO DRIVE (Mantenha seus segredos configurados) ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id: return None, "Chave não configurada."
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        # Lendo com tratamento de erro para linhas malformadas
        df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
        # LIMPEZA CRÍTICA: Remove espaços e caracteres invisíveis de TODAS as colunas
        df.columns = [str(c).strip().upper().replace('ï»¿', '') for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, str(e)

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def executar():
    st.set_page_config(page_title="Radar Core Essence", layout="wide")
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    with st.sidebar:
        st.header("📍 Filtros")
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        ano_sel = st.selectbox("Ano", [2026, 2025, 2024], index=0)
        meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Mês", meses)

    id_chave = FONTES_DADOS[fonte_sel]
    df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- BUSCA FLEXÍVEL DE COLUNAS (O SEGREDO ESTÁ AQUI) ---
        def encontrar_coluna(termos_busca):
            for col in df_base.columns:
                if all(termo in col for termo in termos_busca):
                    return col
            return None

        # Procura as colunas reais no seu arquivo
        col_v_emp = encontrar_coluna(["VALOR", "EMPENHADO"])
        col_v_pag = encontrar_coluna(["VALOR", "PAGO"])
        col_autor = encontrar_coluna(["NOME", "AUTOR"])
        col_mun   = encontrar_coluna(["MUNICÍPIO"])
        col_ano   = encontrar_coluna(["ANO", "EMENDA"]) or encontrar_coluna(["ANO"])
        col_mes   = encontrar_coluna(["MES"])

        if col_v_emp:
            # Tratamento numérico
            for c in [col_v_emp, col_v_pag]:
                if c:
                    df_base[c] = df_base[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_base[c] = pd.to_numeric(df_base[c], errors='coerce').fillna(0)

            # --- FILTRAGEM ---
            df_ano = df_base[df_base[col_ano] == ano_sel] if col_ano else df_base
            df_mes = df_ano[df_ano[col_mes] == mes_sel] if (col_mes and mes_sel != "Todos") else df_ano

            # --- CARDS DE RESUMO ---
            st.subheader(f"📌 Indicadores: {ano_sel}")
            v_ano = df_ano[col_v_emp].sum()
            v_mes_emp = df_mes[col_v_emp].sum()
            v_mes_pag = df_mes[col_v_pag].sum() if col_v_pag else 0
            
            k1, k2, k3 = st.columns(3)
            with k1: st.metric(f"Acumulado Ano ({ano_sel})", formatar_brl(v_ano))
            with k2: st.metric(f"Reservado no Mês", formatar_brl(v_mes_emp))
            with k3: st.metric(f"Efetivamente Pago (Mês)", formatar_brl(v_mes_pag))

            st.markdown("---")

            if not df_mes.empty:
                c1, c2 = st.columns(2)
                with c1:
                    st.write("📊 **Top 10 Autores**")
                    if col_autor:
                        chart = df_mes.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart)
                with c2:
                    st.write("📋 **Distribuição Regional**")
                    if col_mun:
                        chart_mun = df_mes.groupby(col_mun)[col_v_emp].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_mun)

                st.write("### 🔍 Detalhamento das Emendas")
                st.dataframe(df_mes, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado para o mês selecionado.")
        else:
            st.error(f"Não conseguimos identificar as colunas de VALOR no arquivo. Colunas lidas: {list(df_base.columns)}")
    else:
        st.error(f"Erro: {msg}")

if __name__ == "__main__":
    executar()
