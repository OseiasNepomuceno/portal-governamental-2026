import streamlit as st
import pandas as pd
import gdown
import os

# --- CONFIGURAÇÃO DE FONTES (IDs do Drive) ---
# Certifique-se de que estes nomes batem EXATAMENTE com o seu Secrets
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id:
        return None, f"Chave {id_secret} não configurada."
    
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    
    try:
        # Download silencioso
        gdown.download(url, output, quiet=True, fuzzy=True)
        
        if not os.path.exists(output):
            return None, "Arquivo não foi baixado do Drive."

        df = pd.read_csv(output, sep=';', encoding='latin1', low_memory=False)
        df.columns = [c.replace('ï»¿', '').strip().upper() for c in df.columns]
        
        # Garante colunas mínimas para o filtro não quebrar
        if 'ANO' not in df.columns: df['ANO'] = 2026
        if 'MES' not in df.columns: df['MES'] = "Janeiro" 
            
        return df, "Sucesso"
    except Exception as e:
        return None, str(e)

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def executar():
    st.set_page_config(page_title="Radar Core Essence", layout="wide")
    
    st.title("🏛️ Radar de Emendas Parlamentares")
    st.caption("CORE ESSENCE - Inteligência em Gestão Pública")
    st.markdown("---")

    # --- SIDEBAR: FILTROS ---
    with st.sidebar:
        st.header("📍 Filtros de Análise")
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
        
        meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Mês de Referência", meses)
        
        st.write("---")
        st.info("O relatório é atualizado automaticamente ao alterar os filtros acima.")

    # --- PROCESSAMENTO LOGO ABAIXO DOS FILTROS ---
    id_chave = FONTES_DADOS[fonte_sel]
    
    with st.spinner("🛰️ Sincronizando dados com o Drive..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # Identificar colunas de valor e autor
        col_v = next((c for c in ['VALOR_REPASSE_PROPOSTA_EMENDA', 'VALOR_EMENDA', 'VALOR_CONVENIO', 'VALOR_PAGO', 'VALOR_REPASSE'] if c in df_base.columns), None)
        col_a = next((c for c in ['NOME_PARLAMENTAR', 'AUTOR', 'NOME_FAVORECIDO', 'BENEFICIARIO', 'NOME_ORGAO_SUPERIOR'] if c in df_base.columns), None)

        if col_v:
            # Limpeza numérica
            df_base[col_v] = df_base[col_v].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_base[col_v] = pd.to_numeric(df_base[col_v], errors='coerce').fillna(0)

            # --- FILTRAGEM ---
            df_ano = df_base[df_base['ANO'] == ano_sel]
            df_mes = df_ano[df_ano['MES'] == mes_sel] if mes_sel != "Todos" else df_ano

            # --- ÁREA PRINCIPAL (LADO DIREITO) ---
            st.subheader(f"📌 Indicadores Financeiros: {fonte_sel}")
            
            soma_ano = df_ano[col_v].sum()
            soma_mes = df_mes[col_v].sum()
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(f"Total Acumulado {ano_sel}", formatar_brl(soma_ano))
            with kpi2:
                st.metric(f"Total em {mes_sel}", formatar_brl(soma_mes))
            with kpi3:
                st.metric("Qtd. Registros", f"{len(df_mes)} itens")

            st.markdown("---")

            if not df_mes.empty:
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write(f"📊 **Top 10: {fonte_sel}**")
                    if col_a:
                        chart_data = df_mes.groupby(col_a)[col_v].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_data)
                
                with c2:
                    st.write("📋 **Prévia dos Dados**")
                    cols_show = [c for c in [col_a, col_v, 'UF', 'NOME_MUNICIPIO'] if c in df_mes.columns]
                    st.dataframe(df_mes[cols_show].head(20), use_container_width=True)

                st.write("### 🔍 Detalhamento Completo")
                st.dataframe(df_mes, use_container_width=True)
            else:
                st.warning(f"Nenhum dado encontrado para os filtros: {mes_sel} de {ano_sel}.")
        else:
            st.error(f"Coluna de valor não encontrada no arquivo. Colunas disponíveis: {df_base.columns.tolist()}")
    else:
        st.error(f"Não foi possível exibir o relatório. Motivo: {msg}")

if __name__ == "__main__":
    executar()
