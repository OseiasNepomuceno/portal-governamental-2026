import streamlit as st
import pandas as pd
import gdown
import os

# --- CONFIGURAÇÃO DE FONTES (IDs do Drive) ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO",
    "Convênios (Detalhado)": "ID_EMENDAS_CONVENIOS"
}

@st.cache_data(ttl=600, show_spinner="Sincronizando base de dados...")
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id:
        st.error(f"Configuração {id_secret} não encontrada nos Secrets.")
        return None
    
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    
    try:
        if os.path.exists(output): os.remove(output)
        gdown.download(url, output, quiet=False, fuzzy=True)
        
        df = pd.read_csv(output, sep=';', encoding='latin1', low_memory=False)
        df.columns = [c.replace('ï»¿', '').strip().upper() for c in df.columns]
        
        # Garantir que existam colunas de tempo (Simulado se não houver no CSV)
        if 'ANO' not in df.columns: df['ANO'] = 2026
        # Se o seu CSV tiver uma coluna de data, podemos extrair o mês real aqui
        if 'MES' not in df.columns: df['MES'] = "Janeiro" 
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def formatar_brl(valor):
    """Formata número para o padrão de moeda R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def executar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    st.caption("CORE ESSENCE - Gestão Estratégica de Recursos Públicos")
    st.markdown("---")

    # --- SIDEBAR: FILTROS ---
    with st.sidebar:
        st.header("📍 Filtros de Análise")
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
        
        meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Mês de Referência", meses)
        
        btn_processar = st.button("🔍 Gerar Relatório")

    if btn_processar:
        id_chave = FONTES_DADOS[fonte_sel]
        df_base = carregar_dados_drive(id_chave)
        
        if df_base is not None:
            # 1. Identificar colunas de valor e autor
            col_v = next((c for c in ['VALOR_REPASSE_PROPOSTA_EMENDA', 'VALOR_EMENDA', 'VALOR_CONVENIO', 'VALOR_PAGO'] if c in df_base.columns), None)
            col_a = next((c for c in ['NOME_PARLAMENTAR', 'AUTOR', 'NOME_FAVORECIDO', 'BENEFICIARIO'] if c in df_base.columns), None)

            if col_v:
                # Limpeza numérica
                df_base[col_v] = df_base[col_v].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df_base[col_v] = pd.to_numeric(df_base[col_v], errors='coerce').fillna(0)

                # --- LÓGICA DE FILTRAGEM ---
                df_ano = df_base[df_base['ANO'] == ano_sel]
                df_mes = df_ano[df_ano['MES'] == mes_sel] if mes_sel != "Todos" else df_ano

                # --- CARDS SUPERIORES (KPIs) ---
                st.subheader(f"📌 Resumo Financeiro - {fonte_sel}")
                kpi1, kpi2, kpi3 = st.columns(3)
                
                soma_ano = df_ano[col_v].sum()
                soma_mes = df_mes[col_v].sum()
                
                with kpi1:
                    st.info(f"📅 Total Acumulado {ano_sel}")
                    st.subheader(formatar_brl(soma_ano))
                
                with kpi2:
                    st.success(f"🗓️ Total em {mes_sel}")
                    st.subheader(formatar_brl(soma_mes))
                
                with kpi3:
                    st.warning("📈 Registros")
                    st.subheader(f"{len(df_mes)} itens")

                st.markdown("---")

                # --- GRÁFICOS E TABELAS ---
                if not df_mes.empty:
                    col_esq, col_dir = st.columns([1, 1])
                    
                    with col_esq:
                        st.write(f"📊 **Top 10: {fonte_sel}**")
                        if col_a:
                            chart_data = df_mes.groupby(col_a)[col_v].sum().sort_values(ascending=False).head(10)
                            st.bar_chart(chart_data)
                    
                    with col_dir:
                        st.write("📋 **Últimas Movimentações**")
                        # Exibe as colunas mais importantes na prévia
                        cols_prio = [c for c in [col_a, col_v, 'FUNCAO', 'UF'] if c in df_mes.columns]
                        st.dataframe(df_mes[cols_prio].head(15), use_container_width=True)

                    st.write("### 🔍 Detalhamento Completo")
                    st.dataframe(df_mes, use_container_width=True)
                else:
                    st.info(f"Sem movimentações registradas para {mes_sel}/{ano_sel}.")

if __name__ == "__main__":
    executar()
