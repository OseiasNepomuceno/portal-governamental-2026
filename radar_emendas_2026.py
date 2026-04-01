import streamlit as st
import pandas as pd
import gdown
import os

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
    except Exception as e: return None, f"Erro: {e}"

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def achar(df, termos):
    for col in df.columns:
        if all(t in col for t in termos): return col
    return None

def exibir_radar():
    """Esta função desenha o conteúdo do Radar com mapeamento ultra-flexível"""
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos"
        if fonte_sel != "Visão Geral (Emendas)":
            meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_sel = st.selectbox("Mês de Referência", meses)

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados estratégicos..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- DICIONÁRIO DE MAPEAMENTO DINÂMICO ---
        # Ele tenta encontrar a primeira coluna que contenha esses termos
        col_v_emp = achar(df_base, ["VALOR", "EMPENHADO"]) or \
                    achar(df_base, ["VALOR", "REPASSE"]) or \
                    achar(df_base, ["VALOR", "EMENDA"]) or \
                    achar(df_base, ["VALOR", "CONVENIO"])
        
        col_v_pag = achar(df_base, ["VALOR", "PAGO"]) or achar(df_base, ["VALOR", "LIQUIDADO"])
        
        col_autor = achar(df_base, ["NOME", "AUTOR"]) or achar(df_base, ["PARLAMENTAR"])
        
        # Para a base de Favorecido, o "Destino" é o Nome do Favorecido
        col_dest  = achar(df_base, ["NOME", "FAVORECIDO"]) or \
                    achar(df_base, ["MUNICÍPIO"]) or \
                    achar(df_base, ["MUNICIPIO"]) or \
                    achar(df_base, ["BENEFICIARIO"])

        col_ano   = achar(df_base, ["ANO", "EMENDA"]) or achar(df_base, ["ANO"])
        col_mes   = achar(df_base, ["MES"])

        # Se ele achou pelo menos uma coluna de VALOR, o código segue:
        if col_v_emp:
            # Limpeza de dados numéricos
            for c in [col_v_emp, col_v_pag]:
                if c:
                    df_base[c] = df_base[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_base[c] = pd.to_numeric(df_base[c], errors='coerce').fillna(0)

            # --- FILTRAGEM ---
            # Filtro de Ano
            if col_ano in df_base.columns:
                df_ano = df_base[df_base[col_ano] == ano_sel]
            else:
                df_ano = df_base # Se não houver coluna de ano, mostra tudo
            
            # Filtro de Mês
            df_final = df_ano
            if fonte_sel != "Visão Geral (Emendas)" and mes_sel != "Todos" and col_mes:
                df_final = df_ano[df_ano[col_mes] == mes_sel]

            # --- CARDS DE INDICADORES ---
            v_acumulado = df_ano[col_v_emp].sum()
            v_f_emp = df_final[col_v_emp].sum()
            v_f_pag = df_final[col_v_pag].sum() if col_v_pag else 0

            k1, k2, k3 = st.columns(3)
            label_p = "no Ano" if fonte_sel == "Visão Geral (Emendas)" else f"em {mes_sel}"
            k1.metric(f"Total Acumulado ({ano_sel})", formatar_brl(v_acumulado))
            k2.metric(f"Valor Identificado {label_p}", formatar_brl(v_f_emp))
            k3.metric(f"Valor Pago {label_p}", formatar_brl(v_f_pag))

            st.markdown("---")

            if not df_final.empty:
                g1, g2 = st.columns(2)
                with g1:
                    st.write("📈 **Top 10 Origens (Autores/Programas)**")
                    c_origem = col_autor if col_autor else df_base.columns[0]
                    st.bar_chart(df_final.groupby(c_origem)[col_v_emp].sum().sort_values(ascending=False).head(10))
                
                with g2:
                    st.write("📍 **Top 10 Destinos (Favorecidos/Municípios)**")
                    c_dest = col_dest if col_dest else df_base.columns[1]
                    st.bar_chart(df_final.groupby(c_dest)[col_v_emp].sum().sort_values(ascending=False).head(10))

                st.write("### 🔍 Detalhamento dos Registros")
                st.dataframe(df_final, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            st.error(f"⚠️ Erro crítico: Não encontramos colunas de VALOR neste arquivo. Colunas lidas: {list(df_base.columns)}")
    else:
        st.error(msg)
