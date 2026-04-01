import streamlit as st
import pandas as pd
import gdown
import os

# --- IDs DO DRIVE ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id: return None, "Chave não configurada."
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        try:
            df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
            if len(df.columns) < 2: raise ValueError
        except:
            df = pd.read_csv(output, sep=',', encoding='latin1', on_bad_lines='skip', low_memory=False)
        
        df.columns = [str(c).strip().upper().replace('ï»¿', '').replace('"', '') for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, f"Erro: {e}"

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def executar():
    st.set_page_config(page_title="Radar Core Essence", layout="wide")
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    # --- SIDEBAR COM LÓGICA CONDICIONAL ---
    with st.sidebar:
        st.header("📍 Filtros de Análise")
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
        
        # O FILTRO DE MÊS SÓ APARECE SE NÃO FOR A VISÃO GERAL
        mes_sel = "Todos" # Padrão para Visão Geral
        if fonte_sel != "Visão Geral (Emendas)":
            meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_sel = st.selectbox("Mês de Referência", meses)
        
        st.write("---")
        st.info("A Dashboard atualiza automaticamente conforme a base selecionada.")

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # Funções de busca de colunas
        def achar(termos):
            for col in df_base.columns:
                if all(t in col for t in termos): return col
            return None

        col_v_emp = achar(["VALOR", "EMPENHADO"]) or achar(["VALOR", "REPASSE"]) or achar(["VALOR", "EMENDA"])
        col_v_pag = achar(["VALOR", "PAGO"])
        col_autor = achar(["NOME", "AUTOR"]) or achar(["PARLAMENTAR"])
        col_mun   = achar(["MUNICÍPIO"]) or achar(["MUNICIPIO"])
        col_ano   = achar(["ANO", "EMENDA"]) or achar(["ANO"])
        col_mes   = achar(["MES"])

        if col_v_emp:
            # Limpeza numérica
            for c in [col_v_emp, col_v_pag]:
                if c:
                    df_base[c] = df_base[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_base[c] = pd.to_numeric(df_base[c], errors='coerce').fillna(0)

            # --- FILTRAGEM ---
            df_ano = df_base[df_base[col_ano] == ano_sel] if col_ano in df_base.columns else df_base
            
            # Filtra por mês apenas se o filtro existir na tela e a coluna existir no CSV
            df_final = df_ano
            if fonte_sel != "Visão Geral (Emendas)" and mes_sel != "Todos" and col_mes:
                df_final = df_ano[df_ano[col_mes] == mes_sel]

            # --- CARDS DE INDICADORES ---
            st.subheader(f"📊 Dashboard: {fonte_sel}")
            v_acumulado = df_ano[col_v_emp].sum()
            v_filtrado_emp = df_final[col_v_emp].sum()
            v_filtrado_pag = df_final[col_v_pag].sum() if col_v_pag else 0

            c1, c2, c3 = st.columns(3)
            with c1: st.metric(f"Total Acumulado ({ano_sel})", formatar_brl(v_acumulado))
            
            # Se for Visão Geral, o Card 2 e 3 mostram dados do Ano, se for as outras, mostram do Mês
            label_periodo = "no Ano" if fonte_sel == "Visão Geral (Emendas)" else f"em {mes_sel}"
            with c2: st.metric(f"Reservado {label_periodo}", formatar_brl(v_filtrado_emp))
            with c3: st.metric(f"Pago {label_periodo}", formatar_brl(v_filtrado_pag))

            st.markdown("---")

            if not df_final.empty:
                g1, g2 = st.columns(2)
                with g1:
                    st.write("📈 **Ranking de Origem (Autores)**")
                    if col_autor:
                        st.bar_chart(df_final.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10))
                with g2:
                    st.write("📍 **Ranking de Destino (Municípios)**")
                    if col_mun:
                        st.bar_chart(df_final.groupby(col_mun)[col_v_emp].sum().sort_values(ascending=False).head(10))

                st.write("### 🔍 Detalhamento dos Dados")
                st.dataframe(df_final, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado para os critérios selecionados.")
        else:
            st.error(f"Não foi possível identificar colunas de valor nesta base. Colunas: {list(df_base.columns)}")
    else:
        st.error(f"Erro ao carregar base: {msg}")

if __name__ == "__main__":
    executar()
