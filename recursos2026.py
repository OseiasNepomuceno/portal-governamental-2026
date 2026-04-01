import streamlit as st
import pandas as pd
import gdown
import os

# --- FUNÇÃO DE LIMPEZA MONETÁRIA ---
def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0":
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').strip()
        if ',' in v and '.' in v:
            v = v.replace('.', '').replace(',', '.')
        elif ',' in v:
            v = v.replace(',', '.')
        return float(v)
    except:
        return 0.0

# --- CARREGAMENTO DO ARQUIVO ESPECÍFICO DO DRIVE ---
@st.cache_data(ttl=600) # Atualiza a cada 10 minutos se o arquivo mudar no Drive
def carregar_dados_drive():
    # Nome exato do arquivo que você definiu
    nome_arquivo = "20260320_Convenios.csv"
    
    # IMPORTANTE: Certifique-se que o ID abaixo corresponde ao arquivo 20260320_Convenios.csv
    # Se o ID mudar, basta substituir aqui
    file_id = '13Ekq0dn38mZ99Zz_V5zYmW7og3hS24cN' 
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Leitura com tratamento de encoding para arquivos brasileiros (latin1 ou utf-8)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        
        # Padronização de colunas (Ajuste conforme os nomes reais no seu CSV)
        # Vamos tentar identificar colunas de valor e data automaticamente
        df.columns = [c.strip().upper() for c in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {nome_arquivo}: {e}")
        return pd.DataFrame()

def exibir_radar():
    st.title("🛰️ Monitoramento de Recursos (Base: 20260320)")
    st.caption("CORE ESSENCE - Inteligência de Dados Atualizada")

    df_base = carregar_dados_drive()

    if not df_base.empty:
        # Identificando colunas dinamicamente
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_favorecido = next((c for c in df_base.columns if 'FAVORECIDO' in c), None)
        col_tipo = next((c for c in df_base.columns if 'TIPO' in c), None)

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)
        
        # --- ÁREA DE FILTROS ---
        st.markdown("### 🔍 Pesquisa Rápida")
        termo = st.text_input("Filtrar por Favorecido ou Tipo de Recurso:", "").upper()
        
        df_filtrado = df_base
        if termo:
            mask = df_base.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_filtrado = df_base[mask]

        # --- EXIBIÇÃO DE RESULTADOS ---
        c1, c2 = st.columns(2)
        if 'VALOR_NUM' in df_filtrado.columns:
            total = df_filtrado['VALOR_NUM'].sum()
            valor_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            c1.metric("Total Identificado", valor_formatado)
        
        c2.metric("Registros Encontrados", len(df_filtrado))

        st.markdown("---")
        st.subheader("📋 Detalhamento dos Dados")
        
        # Seleciona apenas as colunas mais importantes para não poluir a tela
        colunas_uteis = [c for c in [col_tipo, col_favorecido, col_valor] if c is not None]
        if not colunas_uteis:
            colunas_uteis = df_filtrado.columns[:4] # Mostra as 4 primeiras se não achar nomes padrão
            
        st.dataframe(df_filtrado[colunas_uteis], use_container_width=True)

    else:
        st.warning("Aguardando carregamento da base 20260320_Convenios.csv...")

if __name__ == "__main__":
    exibir_radar()
