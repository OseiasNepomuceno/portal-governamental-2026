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
        df = pd.read_csv(output, sep=';', encoding='latin1', on_bad_lines='skip', low_memory=False)
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
    
    plano_user = str(st.session_state.get('usuario_plano', 'BRONZE')).upper()
    usuario_info = st.session_state.get('usuario_logado', {})
    local_liberado = str(usuario_info.get('local_liberado', '')).upper().strip()

    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**Nível de Acesso:** `{plano_user}`")
        if local_liberado and local_liberado != "NAN":
            label_local = "Estado" if "PRATA" in plano_user else "Localidade(s) Liberada(s)"
            st.info(f"📍 **{label_local}:**\n{local_liberado}")
        st.markdown("---")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos"

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados de alta volumetria..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        C_UF = "UF"
        C_MUN = "MUNICÍPIO"
        C_ANO = "ANO DA EMENDA"
        C_VALOR = "VALOR EMPENHADO"
        C_AUTOR = "NOME DO AUTOR DA EMENDA"

        # --- 1. LIMPEZA DE DADOS ---
        termos_nulos = ["SEM INFORMAÇÃO", "SEM INFORMACAO", "NÃO INFORMADO", "NAN", "NONE", "0", "0.0"]
        for col in [C_UF, C_MUN, C_AUTOR]:
            if col in df_base.columns:
                df_base[col] = df_base[col].astype(str).str.upper().str.strip()
                df_base = df_base[~df_base[col].isin(termos_nulos)]

        # --- 2. TRAVA DE SEGURANÇA (BRONZE, PRATA E OURO) ---
        if local_liberado and local_liberado != "NAN" and "DIAMANTE" not in plano_user:
            locais = [l.strip().upper() for l in local_liberado.split(',')]
            tradutor_uf = {"RJ": "RIO DE JANEIRO", "SP": "SÃO PAULO", "MG": "MINAS GERAIS"}
            
            if "BRONZE" in plano_user:
                if C_MUN in df_base.columns:
                    df_base = df_base[df_base[C_MUN].isin(locais)]
            elif "PRATA" in plano_user:
                if C_UF in df_base.columns:
                    uf_alvo = locais[0]
                    nome_ext = tradutor_uf.get(uf_alvo, uf_alvo)
                    df_base = df_base[(df_base[C_UF] == uf_alvo) | (df_base[C_UF] == nome_ext)]
            elif "OURO" in plano_user:
                if C_UF in df_base.columns:
                    lista_extensa = [tradutor_uf.get(x, x) for x in locais]
                    df_base = df_base[(df_base[C_UF].isin(locais)) | (df_base[C_UF].isin(lista_extensa))]

        # --- 3. FILTRO DE ANO ---
        if C_ANO in df_base.columns:
            df_base[C_ANO] = df_base[C_ANO].astype(str).str.strip().str.replace('.0', '', regex=False)
            df_final = df_base[df_base[C_ANO] == str(ano_sel)].copy()
        else:
            df_final = df_base.copy()

        # --- 4. EXIBIÇÃO ---
        col_v = C_VALOR if C_VALOR in df_final.columns else next((c for c in df_final.columns if "VALOR" in c), None)

        if col_v:
            df_final[col_v] = df_final[col_v].apply(limpar_valor_monetario)
            
            if not df_final.empty:
                v_total = df_final[col_v].sum()
                st.metric(f"Total Identificado em {ano_sel}", formatar_brl(v_total))
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    if C_AUTOR in df_final.columns:
                        st.write("📈 **Top Autores**")
                        chart = df_final.groupby(C_AUTOR)[col_v].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart)
                with col_g2:
                    if C_MUN in df_final.columns:
                        st.write("📍 **Top Municípios**")
                        chart_mun = df_final.groupby(C_MUN)[col_v].sum().sort_values(ascending=False).head(10)
                        st.bar_chart(chart_mun)

                # --- O PULO DO GATO PARA EVITAR O ERRO DE 200MB ---
                st.markdown(f"📊 *Exibindo as primeiras 500 linhas de {len(df_final)} totais (Para performance).*")
                st.dataframe(df_final.head(500), use_container_width=True)
            else:
                st.warning(f"Nenhum dado encontrado para {ano_sel}.")
        else:
            st.error("Coluna de valor financeiro não identificada.")
