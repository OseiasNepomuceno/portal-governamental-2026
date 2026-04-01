# "Versão Final Estável - Filtros e Valores OK"
import streamlit as st
import pandas as pd
import gdown
import os

# --- CONFIGURAÇÕES DE DADOS ---
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

def limpar_valor_monetario(v):
    """Transforma qualquer sujeira como 'R$ 1.250,50' em 1250.50"""
    if pd.isna(v) or v is None:
        return 0.0
    
    # Converte para string e limpa tudo que não for número, vírgula ou ponto
    v = str(v).upper().replace('R$', '').replace(' ', '').strip()
    
    if not v or v in ['NAN', 'NONE', 'NULL', '-']:
        return 0.0

    try:
        # Se tiver ponto e vírgula (ex: 1.250,50), remove o ponto e troca vírgula por ponto
        if '.' in v and ',' in v:
            v = v.replace('.', '').replace(',', '.')
        # Se tiver apenas vírgula (ex: 1250,50), troca por ponto
        elif ',' in v:
            v = v.replace(',', '.')
        
        return float(v)
    except Exception:
        return 0.0
def achar(df, termos):
    for col in df.columns:
        if all(t in col for t in termos): return col
    return None

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    # --- FILTROS NO TOPO ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos"
        if fonte_sel != "Visão Geral (Emendas)":
            meses = ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
            mes_sel = st.selectbox("Mês (Referência)", meses)

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados CORE ESSENCE..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        col_v_emp = achar(df_base, ["VALOR", "RECEBIDO"]) or achar(df_base, ["VALOR", "EMPENHADO"]) or achar(df_base, ["VALOR", "REPASSE"])
        col_autor = achar(df_base, ["NOME", "AUTOR"]) or achar(df_base, ["PARLAMENTAR"])
        col_dest  = achar(df_base, ["FAVORECIDO"]) or achar(df_base, ["MUNICÍPIO"])
        col_tempo = achar(df_base, ["ANO", "MÊS"]) or achar(df_base, ["ANO"])

        if col_v_emp:
            # 1. Tratamento de Valor Usando a Função Blindada
            df_base[col_v_emp] = df_base[col_v_emp].apply(limpar_valor_monetario)

           # 2. Separação de Ano/Mês (Lógica de Posição Fixa)
            if col_tempo:
                # Limpa a sujeira da coluna original
                df_base[col_tempo] = df_base[col_tempo].astype(str).str.strip()
                
                # ANO: Pega sempre os 4 primeiros dígitos (Ex: 2026)
                df_base['ANO_REF'] = df_base[col_tempo].str[:4]
                
                # MÊS: Pega sempre os 2 últimos dígitos (Ex: 01)
                # Isso funciona para '2026/01', '2026-01' ou '01'
                df_base['MES_REF'] = df_base[col_tempo].str[-2:].str.strip()

            # 3. Filtragem (Conversão para String Garantida)
            df_final = df_base
            
            # Filtro de Ano
            if 'ANO_REF' in df_base.columns:
                df_final = df_base[df_base['ANO_REF'] == str(ano_sel)]
            
            # Filtro de Mês (Só aplica se não for "Todos")
            if mes_sel != "Todos" and 'MES_REF' in df_base.columns:
                # Forçamos o filtro a ser sempre com 2 dígitos (ex: '01')
                filtro_mes = str(mes_sel).zfill(2)
                df_final = df_final[df_final['MES_REF'] == filtro_mes]

            # --- CARDS DE INDICADORES ---
            v_total = df_final[col_v_emp].sum()
            k1, k2, k3 = st.columns(3)
            label = "no Ano" if mes_sel == "Todos" else f"em {mes_sel}/{ano_sel}"
            
            k1.metric(f"Total Identificado {label}", formatar_brl(v_total))
            k2.metric("Qtd. Registros", f"{len(df_final)}")
            
            media_val = v_total/len(df_final) if len(df_final)>0 else 0
            k3.metric("Média/Repasse", formatar_brl(media_val))

            st.markdown("---")

            if not df_final.empty:
                g1, g2 = st.columns(2)
                with g1:
                    if col_autor:
                        st.write("📈 **Top 10 Autores**")
                        chart_aut = df_final.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_aut)
                with g2:
                    if col_dest:
                        st.write("📍 **Top 10 Destinos**")
                        chart_dest = df_final.groupby(col_dest)[col_v_emp].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_dest)
                
                st.write("### 🔍 Detalhamento")
                st.dataframe(df_final, use_container_width=True)
            else:
                st.warning(f"Nenhum dado financeiro encontrado para {mes_sel}/{ano_sel}.")
        else:
            st.error("Coluna de valor não encontrada.")
    else:
        st.error(f"Erro: {msg}")
