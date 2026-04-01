import streamlit as st
import pandas as pd
import gdown
import os

# --- IDs DO DRIVE (Certifique-se de que estão no seu Secrets do Streamlit Cloud) ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id: 
        return None, f"Chave {id_secret} não configurada nos Secrets."
    
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        if not os.path.exists(output): 
            return None, "Erro ao baixar o arquivo do Google Drive."

        # Tenta ler com ';' (padrão Brasil) ou ',' (padrão Internacional)
        try:
            df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
            if len(df.columns) < 2: raise ValueError
        except:
            df = pd.read_csv(output, sep=',', encoding='latin1', on_bad_lines='skip', low_memory=False)
        
        # Limpeza agressiva dos nomes das colunas
        df.columns = [str(c).strip().upper().replace('ï»¿', '').replace('"', '') for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, f"Erro de leitura: {e}"

def formatar_brl(valor):
    """Formata números para o padrão de moeda brasileiro R$"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def achar(df, termos):
    """Busca uma coluna que contenha todos os termos fornecidos"""
    for col in df.columns:
        if all(t in col for t in termos): return col
    return None

def exibir_radar():
    """Função principal que desenha o Radar no portal"""
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    # --- FILTROS NO TOPO (ÁREA PRINCIPAL) ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos"
        if fonte_sel != "Visão Geral (Emendas)":
            # Meses em formato numérico para bater com a base de Favorecidos (2026/01)
            meses = ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
            mes_sel = st.selectbox("Mês (Referência)", meses)
        else:
            st.info("Filtro de Mês indisponível nesta base.")

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados estratégicos da CORE ESSENCE..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- MAPEAMENTO INTELIGENTE ---
        col_v_emp = achar(df_base, ["VALOR", "RECEBIDO"]) or \
                    achar(df_base, ["VALOR", "EMPENHADO"]) or \
                    achar(df_base, ["VALOR", "REPASSE"])
        
        col_v_pag = achar(df_base, ["VALOR", "PAGO"]) or col_v_emp
        col_autor = achar(df_base, ["NOME", "AUTOR"]) or achar(df_base, ["PARLAMENTAR"])
        col_dest  = achar(df_base, ["FAVORECIDO"]) or achar(df_base, ["MUNICÍPIO"])
        col_tempo = achar(df_base, ["ANO", "MÊS"]) or achar(df_base, ["ANO"])

        if col_v_emp:
            # Tratamento Numérico
            df_base[col_v_emp] = df_base[col_v_emp].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_base[col_v_emp] = pd.to_numeric(df_base[col_v_emp], errors='coerce').fillna(0)

            # --- LÓGICA DE FILTRAGEM (ANO E MÊS) ---
            df_final = df_base
            if col_tempo:
                # Filtra pelo ano contido na string (ex: "2026" em "2026/01")
                df_final = df_base[df_base[col_tempo].
