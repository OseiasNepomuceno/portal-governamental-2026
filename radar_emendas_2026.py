import streamlit as st
import pandas as pd
import gdown
import os

# --- IDs DO DRIVE (Mantenha seus Secrets configurados) ---
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

def radar_emendas_layout():
    """Função interna que desenha o Radar de Emendas com os filtros inteligentes"""
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    # --- FILTROS DENTRO DA ÁREA DO RADAR ---
    with st.expander("🔍 Filtros de Pesquisa Avançada", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        with col2:
            ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
        with col3:
            mes_sel = "Todos"
            if fonte_sel != "Visão Geral (Emendas)":
                meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                mes_sel = st.selectbox("Mês de Referência", meses)
            else:
                st.info("Filtro de Mês não aplicável nesta base.")

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados estratégicos..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
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
            for c in [col_v_emp, col_v_pag]:
                if c:
                    df_base[c] = df_base[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_base[c] = pd.to_numeric(df_base[c], errors='coerce').fillna(0)

            df_ano = df_base[df_base[col_ano] == ano_sel] if col_ano in df_base.columns else df_base
            df_final = df_ano
            if fonte_sel != "Visão Geral (Emendas)" and mes_sel != "Todos" and col_mes:
                df_final = df_ano[df_ano[col_mes] == mes_sel]

            # --- CARDS DE INDICADORES ---
            v_acumulado = df_ano[col_v_emp].sum()
            v_filtrado_emp = df_final[col_v_emp].sum()
            v_filtrado_pag = df_final[col_v_pag].sum() if col_v_pag else 0

            k1, k2, k3 = st.columns(3)
            label_p = "no Ano" if fonte_sel == "Visão Geral (Emendas)" else f"em {mes_sel}"
            k1.metric(f"Total Acumulado ({ano_sel})", formatar_brl(v_acumulado))
            k2.metric(f"Reservado {label_p}", formatar_brl(v_filtrado_emp))
            k3.metric(f"Pago {label_p}", formatar_brl(v_filtrado_pag))

            st.markdown("---")

            if not df_final.empty:
                g1, g2 = st.columns(2)
                with g1:
                    st.write("📈 **Top 10 Autores**")
                    if col_autor:
                        st.bar_chart(df_final.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10))
                with g2:
                    st.write("📍 **Top 10 Municípios**")
                    if col_mun:
                        st.bar_chart(df_final.groupby(col_mun)[col_v_emp].sum().sort_values(ascending=False).head(10))

                st.write("### 🔍 Detalhamento dos Dados")
                st.dataframe(df_final, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado.")
        else:
            st.error("Erro ao mapear colunas de valor.")
    else:
        st.error(msg)

def executar():
    """Função principal que reconstrói o seu menu lateral original"""
    st.set_page_config(page_title="Core Essence - Gestão", layout="wide")

    # --- BARRA LATERAL (NAVEGAÇÃO ORIGINAL) ---
    with st.sidebar:
        st.image("https://via.placeholder.com/150", caption="CORE ESSENCE") # Troque pela sua logo
        st.title("Menu Principal")
        
        menu_opcoes = ["📊 Recursos", "🏛️ Emendas", "📜 Revisão de Estatuto", "⚙️ Gestão", "🚪 Sair"]
        escolha = st.radio("Selecione um módulo:", menu_opcoes)

    # --- LÓGICA DE EXIBIÇÃO DO CONTEÚDO ---
    if escolha == "📊 Recursos":
        st.title("Recursos do Sistema")
        st.info("Módulo de gestão de recursos financeiros em desenvolvimento.")
        
    elif escolha == "🏛️ Emendas":
        # AQUI CHAMAMOS O RADAR QUE ACABAMOS DE CONSTRUIR
        radar_emendas_layout()
        
    elif escolha == "📜 Revisão de Estatuto":
        st.title("Revisão de Estatuto")
        st.write("Conteúdo para análise e revisão de estatutos jurídicos.")
        
    elif escolha == "⚙️ Gestão":
        st.title("Configurações de Gestão")
        st.write("Painel administrativo.")
        
    elif escolha == "🚪 Sair":
        st.write("Sessão finalizada. Por favor, feche o navegador.")
        st.stop()

if __name__ == "__main__":
    executar()
