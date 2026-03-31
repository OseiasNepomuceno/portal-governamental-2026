import streamlit as st
import pandas as pd
import gdown
import os

# --- DICIONÁRIO DE ARQUIVOS ---
FONTES_DADOS = {
    "Visão Geral": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600, show_spinner="Sincronizando base de dados...")
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id:
        st.error(f"Configuração {id_secret} não encontrada.")
        return None
    
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    
    try:
        if os.path.exists(output): os.remove(output)
        gdown.download(url, output, quiet=False, fuzzy=True)
        
        # Leitura com tratamento de encoding do Governo
        df = pd.read_csv(output, sep=';', encoding='latin1', low_memory=False)
        df.columns = [c.replace('ï»¿', '').strip().upper() for c in df.columns]
        
        # --- LÓGICA DE DATA ---
        # Como o CSV não tem data, vamos simular para o filtro funcionar
        # Se houver uma coluna de data real no arquivo, o código abaixo deve ser ajustado
        if 'ANO' not in df.columns:
            df['ANO'] = 2026
        if 'MES' not in df.columns:
            # Simulando meses para demonstração, ou você pode extrair de colunas de registro
            df['MES'] = "Janeiro" 
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {id_secret}: {e}")
        return None

def executar():
    st.title("🏛️ Radar de Emendas Parlamentares 2026")
    st.caption("CORE ESSENCE - Inteligência Governamental e Análise Orçamentária")
    st.markdown("---")

    # --- MENU LATERAL (FILTROS) ---
    with st.sidebar:
        st.header("🔍 Filtros de Busca")
        
        # Filtro 1: Fonte de Dados
        fonte_sel = st.selectbox("Selecione a Visão:", list(FONTES_DADOS.keys()))
        
        # Filtro 2: Ano
        ano_sel = st.selectbox("Ano", [2026, 2025, 2024], index=0)
        
        # Filtro 3: Mês
        meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Mês", meses)
        
        btn_atualizar = st.button("🚀 Aplicar Filtros")

    if btn_atualizar:
        id_chave = FONTES_DADOS[fonte_sel]
        df = carregar_dados_drive(id_chave)
        
        if df is not None:
            # --- APLICANDO FILTROS NO DATAFRAME ---
            df_filt = df[df['ANO'] == ano_sel]
            
            if mes_sel != "Todos":
                # Nota: Certifique-se que seu CSV tenha algo que identifique o mês
                if 'MES' in df_filt.columns:
                    df_filt = df_filt[df_filt['MES'] == mes_sel]

            # --- ÁREA DE RESULTADOS (LADO DIREITO) ---
            if not df_filt.empty:
                st.subheader(f"📊 Resultados: {fonte_sel} ({mes_sel}/{ano_sel})")
                
                # Identificando colunas dinamicamente para o gráfico
                col_valor = ""
                for c in ['VALOR_REPASSE_PROPOSTA_EMENDA', 'VALOR_EMENDA', 'VALOR_CONVENIO']:
                    if c in df_filt.columns:
                        col_valor = c
                        break
                
                col_autor = ""
                for c in ['NOME_PARLAMENTAR', 'AUTOR', 'NOME_AUTOR']:
                    if c in df_filt.columns:
                        col_autor = c
                        break

                if col_valor and col_autor:
                    # Limpeza de valor
                    df_filt[col_valor] = df_filt[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_filt[col_valor] = pd.to_numeric(df_filt[col_valor], errors='coerce').fillna(0)
                    
                    # Métricas
                    total = df_filt[col_valor].sum()
                    m1, m2 = st.columns(2)
                    m1.metric("Volume Total", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    m2.metric("Qtd. de Registros", len(df_filt))
                    
                    # Gráfico
                    st.bar_chart(df_filt.groupby(col_autor)[col_valor].sum().sort_values(ascending=False).head(10))
                
                st.write("### 📋 Dados Detalhados")
                st.dataframe(df_filt, use_container_width=True)
            else:
                st.info(f"Nenhum dado encontrado para {mes_sel}/{ano_sel} nesta visão.")

if __name__ == "__main__":
    executar()
