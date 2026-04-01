import streamlit as st
import pandas as pd
import gdown
import os

# --- FUNÇÃO DE LIMPEZA MONETÁRIA ---
def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0":
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except:
        return 0.0

@st.cache_data(ttl=600)
def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Leitura da base
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        if len(df.columns) <= 1:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip')

        # Padroniza nomes das colunas para MAIÚSCULO e sem espaços
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # --- TRATAMENTO DO ANO (Extração da Data 00/00/0000) ---
        # Procura colunas que tenham DATA no nome para extrair o Ano
        col_data_bruta = next((c for c in df.columns if 'DATA' in c or 'DT_' in c), None)
        
        if col_data_bruta:
            # Converte para formato de data e extrai o ano
            df['ANO_FILTRO'] = pd.to_datetime(df[col_data_bruta], dayfirst=True, errors='coerce').dt.year
            # Remove valores nulos e converte para texto (para o filtro ficar bonito)
            df = df.dropna(subset=['ANO_FILTRO'])
            df['ANO_FILTRO'] = df['ANO_FILTRO'].astype(int).astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar base: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Radar de Recursos Governamentais")
    st.caption("CORE ESSENCE - Filtros de Precisão Executiva")

    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- DEFINIÇÃO DAS COLUNAS ---
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = 'ANO_FILTRO' if 'ANO_FILTRO' in df_base.columns else None
        col_uf = 'UF' if 'UF' in df_base.columns else None # Travado em UF como solicitado
        col_mun = next((c for c in df_base.columns if any(x in c for x in ['MUNICIPIO', 'CIDADE', 'MUNIC'])), None)

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        # --- INTERFACE DE FILTROS ---
        st.markdown("### 🔍 Painel de Auditoria")
        termo = st.text_input("1. Pesquisa Geral (Favorecido/Objeto):").upper()
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", opcoes_ano)

        with c2:
            opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", opcoes_uf)

        with c3:
            opcoes_mun = ["Todos"] + sorted(df_base[col_mun].dropna().unique().astype(str).tolist()) if col_mun else ["Todos"]
            filtro_mun = st.selectbox("4. Cidade:", opcoes_mun)

        # --- APLICAÇÃO DA FILTRAGEM ---
        df_f = df_base.copy()
        
        if termo:
            mask = df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_f = df_f[mask]
        
        if filtro_ano != "Todos":
            df_f = df_f[df_f[col_ano] == filtro_ano]
            
        if filtro_uf != "Todos":
            df_f = df_f[df_f[col_uf] == filtro_uf]
            
        if filtro_mun != "Todos":
            df_f = df_f[df_f[col_mun] == filtro_mun]

        # --- EXIBIÇÃO DE INDICADORES ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_f.columns:
            total_filtrado = df_f['VALOR_NUM'].sum()
            k1.metric("Total Identificado", f"R$ {total_filtrado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Registros", len(df_f))

        st.dataframe(df_f, use_container_width=True)
    else:
        st.info("Aguardando carregamento da base 20260320_Convenios.csv...")

if __name__ == "__main__":
    exibir_radar()
