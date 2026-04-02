# "Versão Final Estável - Filtros de Segurança Integrados"
import streamlit as st
import pandas as pd
import gdown
import os

# --- CONFIGURAÇÕES DE DADOS (AJUSTADO: REMOVIDO CONVÊNIOS) ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO"
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
        
        # Padronização de colunas
        df.columns = [str(c).strip().upper().replace('ï»¿', '').replace('"', '') for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, f"Erro: {e}"

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def limpar_valor_monetario(v):
    if pd.isna(v) or v is None:
        return 0.0
    v = str(v).upper().replace('R$', '').replace(' ', '').strip()
    if not v or v in ['NAN', 'NONE', 'NULL', '-']:
        return 0.0
    try:
        if '.' in v and ',' in v:
            v = v.replace('.', '').replace(',', '.')
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
    
    # --- 1. IDENTIFICAÇÃO DO USUÁRIO E PLANO ---
    usuario = st.session_state.get('usuario_logado')
    plano_user = str(st.session_state.get('usuario_plano', 'BRONZE')).upper()
    local_liberado = ""
    if usuario and 'local_liberado' in usuario:
        local_liberado = str(usuario['local_liberado']).upper()

    # --- FILTROS NO TOPO ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        # Aqui o selectbox usará o dicionário já sem a opção de Convênios
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
        # --- 2. APLICAÇÃO DA TRAVA DE SEGURANÇA ---
        col_uf = achar(df_base, ["UF"]) or "UF"
        col_mun = achar(df_base, ["MUNICÍPIO"]) or achar(df_base, ["CIDADE"]) or "NOME MUNICÍPIO"

        if local_liberado and local_liberado != "NAN" and "DIAMANTE" not in plano_user:
            if "BRONZE" in plano_user:
                cidades = [c.strip() for c in local_liberado.split(',')]
                if col_mun in df_base.columns:
                    df_base = df_base[df_base[col_mun].astype(str).str.upper().isin(cidades)]
                    st.sidebar.warning(f"📍 Cidades liberadas: {len(cidades)}")
            
            elif "PRATA" in plano_user:
                if col_uf in df_base.columns:
                    df_base = df_base[df_base[col_uf].astype(str).str.upper() == local_liberado]
                    st.sidebar.info(f"📍 Estado liberado: {local_liberado}")

            elif "OURO" in plano_user:
                estados = [e.strip() for e in local_liberado.split(',')]
                if col_uf in df_base.columns:
                    df_base = df_base[df_base[col_uf].astype(str).str.upper().isin(estados)]
                    st.sidebar.info(f"📍 Estados liberados: {len(estados)}")

        # --- PROCESSAMENTO DOS DADOS FILTRADOS ---
        col_v_emp = achar(df_base, ["VALOR", "RECEBIDO"]) or achar(df_base, ["VALOR", "EMPENHADO"]) or achar(df_base, ["VALOR", "REPASSE"])
        col_autor = achar(df_base, ["NOME", "AUTOR"]) or achar(df_base, ["PARLAMENTAR"])
        col_dest  = achar(df_base, ["FAVORECIDO"]) or achar(df_base, ["MUNICÍPIO"])
        col_tempo = achar(df_base, ["ANO", "MÊS"]) or achar(df_base, ["ANO"])

        if col_v_emp:
            df_base[col_v_emp] = df_base[col_v_emp].apply(limpar_valor_monetario)

            if col_tempo:
                df_base[col_tempo] = df_base[col_tempo].astype(str).str.strip()
                df_base['ANO_REF'] = df_base[col_tempo].str[:4]
                df_base['MES_REF'] = df_base[col_tempo].str[-2:].str.strip()

            df_final = df_base
            if 'ANO_REF' in df_base.columns:
                df_final = df_base[df_base['ANO_REF'] == str(ano_sel)]
            if mes_sel != "Todos" and 'MES_REF' in df_base.columns:
                filtro_mes = str(mes_sel).zfill(2)
                df_final = df_final[df_final['MES_REF'] == filtro_mes]

            # --- INTERFACE ---
            if not df_final.empty:
                v_total = df_final[col_v_emp].sum()
                k1, k2, k3 = st.columns(3)
                label = "no Ano" if mes_sel == "Todos" else f"em {mes_sel}/{ano_sel}"
                k1.metric(f"Total Identificado {label}", formatar_brl(v_total))
                k2.metric("Qtd. Registros", f"{len(df_final)}")
                media_val = v_total/len(df_final) if len(df_final)>0 else 0
                k3.metric("Média/Repasse", formatar_brl(media_val))

                st.markdown("---")
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
                st.warning(f"Nenhum dado encontrado para os filtros selecionados.")
        else:
            st.error("Coluna de valor não encontrada na base.")
    else:
        st.error(f"Erro ao carregar dados: {msg}")
