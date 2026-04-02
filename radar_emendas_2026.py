import streamlit as st
import pandas as pd
import gdown
import os

# --- CONFIGURAÇÕES DE DADOS ---
FONTES_DADOS = {
    "Visão Geral (Emendas)": "ID_EMENDAS_GERAL",
    "Por Favorecido (Quem recebe)": "ID_EMENDAS_FAVORECIDO"
}

@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados_drive(id_secret):
    file_id = st.secrets.get(id_secret)
    if not file_id: 
        return None, f"Chave {id_secret} não configurada."
    url = f'https://drive.google.com/uc?export=download&id={file_id}'
    output = f"{id_secret}.csv"
    try:
        gdown.download(url, output, quiet=True, fuzzy=True)
        # Forçamos o separador ';' que você confirmou no bloco de notas
        df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
        
        # Limpeza de nomes de colunas (Mantemos o padrão para bater com o script)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df, "Sucesso"
    except Exception as e:
        return None, f"Erro na leitura: {e}"

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def limpar_valor_monetario(v):
    if pd.isna(v) or v is None: return 0.0
    v = str(v).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(v)
    except:
        return 0.0

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    usuario = st.session_state.get('usuario_logado')
    plano_user = str(st.session_state.get('usuario_plano', 'BRONZE')).upper()
    local_liberado = str(st.session_state.get('usuario_local', '')).upper()

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos" # Visão Geral não costuma ter mês separado em coluna única

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados CORE ESSENCE..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- MAPEAMENTO COM BASE NO SEU BLOCO DE NOTAS ---
        C_UF = "UF"
        C_MUN = "MUNICÍPIO"
        C_ANO = "ANO DA EMENDA"
        C_VALOR = "VALOR EMPENHADO"
        C_AUTOR = "NOME DO AUTOR DA EMENDA"

        # --- APLICAÇÃO DA SEGURANÇA ---
        if local_liberado and local_liberado != "NAN" and "DIAMANTE" not in plano_user:
            locais = [l.strip().upper() for l in local_liberado.split(',')]
            
            if "BRONZE" in plano_user:
                if C_MUN in df_base.columns:
                    df_base = df_base[df_base[C_MUN].astype(str).str.upper().isin(locais)]
            
            elif "PRATA" in plano_user:
                if C_UF in df_base.columns:
                    uf_alvo = locais[0] # Ex: RJ
                    df_base = df_base[df_base[C_UF].astype(str).str.upper().str.strip() == uf_alvo]
                    st.sidebar.info(f"📍 Estado: {uf_alvo}")

        # --- FILTRO DE ANO ---
        if C_ANO in df_base.columns:
            df_base[C_ANO] = df_base[C_ANO].astype(str).str.strip()
            df_final = df_base[df_base[C_ANO] == str(ano_sel)]
        else:
            df_final = df_base

        # --- EXIBIÇÃO ---
        if C_VALOR in df_final.columns:
            df_final[C_VALOR] = df_final[C_VALOR].apply(limpar_valor_monetario)
            
            if not df_final.empty:
                v_total = df_final[C_VALOR].sum()
                st.metric(f"Total Identificado em {ano_sel}", formatar_brl(v_total))
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    if C_AUTOR in df_final.columns:
                        st.write("📈 **Top Autores**")
                        chart = df_final.groupby(C_AUTOR)[C_VALOR].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart)
                with col_g2:
                    if C_MUN in df_final.columns:
                        st.write("📍 **Top Municípios**")
                        chart_mun = df_final.groupby(C_MUN)[C_VALOR].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_mun)

                st.dataframe(df_final, use_container_width=True)
            else:
                st.warning(f"Nenhum dado para {ano_sel} com os filtros atuais.")
        else:
            st.error(f"Coluna '{C_VALOR}' não encontrada.")
    else:
        st.error(msg)
