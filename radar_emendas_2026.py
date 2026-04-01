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

@st.cache_data(ttl=600, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id:
        return None, f"Chave {id_secret} não configurada."
    
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        if not os.path.exists(output):
            return None, "Arquivo não encontrado após download."

        # Leitura com o padrão de nomes enviado
        df = pd.read_csv(output, sep=';', encoding='latin1', low_memory=False)
        
        # Limpeza básica de nomes de colunas
        df.columns = [c.strip() for c in df.columns]
            
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

    with st.sidebar:
        st.header("📍 Filtros de Análise")
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
        
        # Baseado no seu arquivo, o Ano está em 'ANO DA EMENDA' ou 'ANO'
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
        
        meses = ["Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_sel = st.selectbox("Mês de Referência", meses)
        
        st.write("---")
        st.info("O relatório é atualizado automaticamente ao alterar os filtros.")

    id_chave = FONTES_DADOS[fonte_sel]
    
    with st.spinner("🛰️ Sincronizando dados estratégicos..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- MAPEAMENTO DE COLUNAS BASEADO NO SEU RETORNO ---
        col_v_emp = 'VALOR EMPENHADO'
        col_v_pag = 'VALOR PAGO'
        col_autor = 'NOME DO AUTOR DA EMENDA'
        col_municipio = 'MUNICÍPIO'

        # Verifica se as colunas essenciais existem
        if col_v_emp in df_base.columns:
            # Limpeza numérica para todas as colunas de valor
            for c_val in [col_v_emp, col_v_pag, 'VALOR LIQUIDADO']:
                if c_val in df_base.columns:
                    df_base[c_val] = df_base[c_val].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_base[c_val] = pd.to_numeric(df_base[c_val], errors='coerce').fillna(0)

            # --- FILTRAGEM (Usando as colunas ANO e MES que você já tem no arquivo) ---
            df_ano = df_base[df_base['ANO DA EMENDA'] == ano_sel]
            if df_ano.empty and 'ANO' in df_base.columns: # Tenta a outra coluna de ano se a primeira falhar
                df_ano = df_base[df_base['ANO'] == ano_sel]
                
            df_mes = df_ano[df_ano['MES'] == mes_sel] if mes_sel != "Todos" else df_ano

            # --- CARDS DE INDICADORES (LADO DIREITO - SUPERIOR) ---
            st.subheader(f"📌 Resumo Financeiro: {ano_sel}")
            
            total_emp_ano = df_ano[col_v_emp].sum()
            total_pag_mes = df_mes[col_v_pag].sum()
            total_emp_mes = df_mes[col_v_emp].sum()
            
            k1, k2, k3 = st.columns(3)
            with k1:
                st.metric(f"Total Reservado (Ano {ano_sel})", formatar_brl(total_emp_ano))
            with k2:
                st.metric(f"Total Reservado no Mês", formatar_brl(total_emp_mes))
            with k3:
                st.metric(f"Total Efetivamente Pago (Mês)", formatar_brl(total_pag_mes))

            st.markdown("---")

            if not df_mes.empty:
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write(f"📊 **Top 10 Autores no Período**")
                    if col_autor in df_mes.columns:
                        chart_data = df_mes.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_data)
                
                with c2:
                    st.write("📋 **Distribuição por Município (Top 10)**")
                    if col_municipio in df_mes.columns:
                        mun_data = df_mes.groupby(col_municipio)[col_v_emp].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(mun_data)

                st.write("### 🔍 Listagem Detalhada das Emendas")
                # Seleciona colunas mais amigáveis para a tabela
                colunas_tabela = [col_autor, col_municipio, 'UF', 'NOME FUNÇÃO', col_v_emp, col_v_pag]
                cols_finais = [c for c in colunas_tabela if c in df_mes.columns]
                st.dataframe(df_mes[cols_finais], use_container_width=True)
            else:
                st.warning(f"Nenhum registro encontrado para {mes_sel} de {ano_sel}.")
        else:
            st.error(f"Erro de Mapeamento: A coluna '{col_v_emp}' não foi encontrada.")
    else:
        st.error(f"Não foi possível carregar os dados: {msg}")

if __name__ == "__main__":
    executar()
