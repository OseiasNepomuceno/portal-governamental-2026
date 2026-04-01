import streamlit as st
import pandas as pd
import gdown
import os

# --- DICIONÁRIO DE IDs (Mantenha seus Secrets configurados) ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id: return None, "Chave não configurada nos Secrets."
    
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        if not os.path.exists(output): return None, "Arquivo não baixado."

        # Tenta ler com ';' (padrão Brasil) e depois com ',' (padrão Internacional)
        try:
            df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
            if len(df.columns) < 2: # Se leu apenas 1 coluna, o separador está errado
                raise ValueError
        except:
            df = pd.read_csv(output, sep=',', encoding='latin1', on_bad_lines='skip', low_memory=False)

        # LIMPEZA AGRESSIVA DE COLUNAS
        df.columns = [str(c).strip().upper().replace('ï»¿', '').replace('"', '') for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, f"Erro de leitura: {e}"

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def executar():
    st.set_page_config(page_title="Radar Core Essence", layout="wide")
    st.title("🏛️ Radar de Emendas Parlamentares")
    st.caption("CORE ESSENCE - Inteligência Orçamentária")

    with st.sidebar:
        st.header("📍 Filtros")
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        ano_sel = st.selectbox("Ano", [2026, 2025, 2024], index=0)
        meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Mês", meses)

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando com a base de dados..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- BUSCA INTELIGENTE POR PALAVRA-CHAVE NAS COLUNAS ---
        def achar(termos):
            for col in df_base.columns:
                if all(t in col for t in termos): return col
            return None

        # Mapeando as colunas que você listou anteriormente
        col_v_emp = achar(["VALOR", "EMPENHADO"])
        col_v_pag = achar(["VALOR", "PAGO"])
        col_autor = achar(["NOME", "AUTOR"]) or achar(["AUTOR"])
        col_mun   = achar(["MUNICÍPIO"]) or achar(["MUNICIPIO"])
        col_ano   = achar(["ANO", "EMENDA"]) or achar(["ANO"])
        col_mes   = achar(["MES"])

        if col_v_emp:
            # Tratamento Numérico (Remove pontos de milhar e converte vírgula decimal)
            for c in [col_v_emp, col_v_pag]:
                if c:
                    df_base[c] = df_base[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_base[c] = pd.to_numeric(df_base[c], errors='coerce').fillna(0)

            # Filtragem Segura
            df_ano = df_base[df_base[col_ano] == ano_sel] if col_ano else df_base
            df_mes = df_ano[df_ano[col_mes] == mes_sel] if (col_mes and mes_sel != "Todos") else df_ano

            # --- EXIBIÇÃO DOS CARDS SUPERIORES ---
            st.subheader(f"📊 Consolidado Financeiro - {ano_sel}")
            v_ano = df_ano[col_v_emp].sum()
            v_mes_emp = df_mes[col_v_emp].sum()
            v_mes_pag = df_mes[col_v_pag].sum() if col_v_pag else 0

            c1, c2, c3 = st.columns(3)
            with c1: st.metric(f"Total Reservado ({ano_sel})", formatar_brl(v_ano))
            with c2: st.metric(f"Reservado no Mês", formatar_brl(v_mes_emp))
            with c3: st.metric(f"Pago no Mês", formatar_brl(v_mes_pag))

            st.markdown("---")

            if not df_mes.empty:
                g1, g2 = st.columns(2)
                with g1:
                    st.write("📈 **Top 10 Autores (Volume R$)**")
                    if col_autor:
                        st.bar_chart(df_mes.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10))
                with g2:
                    st.write("📍 **Top 10 Municípios Beneficiados**")
                    if col_mun:
                        st.bar_chart(df_mes.groupby(col_mun)[col_v_emp].sum().sort_values(ascending=False).head(10))

                st.write("### 🔍 Detalhamento das Emendas")
                st.dataframe(df_mes, use_container_width=True)
            else:
                st.warning(f"Nenhum dado encontrado para {mes_sel}/{ano_sel}.")
        else:
            st.error(f"⚠️ Erro de Mapeamento: Coluna de Valor não identificada. Colunas disponíveis: {list(df_base.columns)}")
    else:
        st.error(f"❌ Erro de Conexão: {msg}")

if __name__ == "__main__":
    executar()
