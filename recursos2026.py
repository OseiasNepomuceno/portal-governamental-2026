import streamlit as st
import pandas as pd
import gdown
import os

# Dicionário de tradução para interface
DE_PARA_UF = {
    'AC': 'ACRE', 'AL': 'ALAGOAS', 'AP': 'AMAPA', 'AM': 'AMAZONAS', 'BA': 'BAHIA',
    'CE': 'CEARA', 'DF': 'DISTRITO FEDERAL', 'ES': 'ESPIRITO SANTO', 'GO': 'GOIAS',
    'MA': 'MARANHAO', 'MT': 'MATO GROSSO', 'MS': 'MATO GROSSO DO SUL', 'MG': 'MINAS GERAIS',
    'PA': 'PARA', 'PB': 'PARAIBA', 'PR': 'PARANA', 'PE': 'PERNAMBUCO', 'PI': 'PIAUI',
    'RJ': 'RIO DE JANEIRO', 'RN': 'RIO GRANDE DO NORTE', 'RS': 'RIO GRANDE DO SUL',
    'RO': 'RONDONIA', 'RR': 'RORAIMA', 'SC': 'SANTA CATARINA', 'SP': 'SAO PAULO',
    'SE': 'SERGIPE', 'TO': 'TOCANTINS'
}

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: 
        return 0.0
    try:
        # Converte R$ 1.234,56 para 1234.56
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: 
        return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos 2026")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convênios.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando Base de Convênios..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    # --- DADOS DO USUÁRIO ---
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper()
    # Pega a sigla da UF do usuário (ex: SP)
    uf_user = str(usuario.get('UF_LIBERADA') or usuario.get('UF') or "SP").strip().upper()
    acesso_nacional = (plano == "PREMIUM" or uf_user == "BRASIL")

    # --- SIDEBAR ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        st.info(f"**LOGIN:** {str(usuario.get('NOME', 'CONSULTOR')).upper()}")
        if acesso_nacional:
            st.success("✅ **PLANO:** PREMIUM (NACIONAL)")
        else:
            st.warning(f"💼 **PLANO:** BÁSICO (ESTADUAL)")
            st.write(f"📍 **UF LIBERADA:** {uf_user} - {DE_PARA_UF.get(uf_user, '')}")
        st.divider()

    colunas_finais = [
        "UF", "NOME MUNICÍPIO", "SITUAÇÃO CONVÊNIO", "OBJETO DO CONVÊNIO", 
        "NOME ÓRGÃO SUPERIOR", "NOME CONVENENTE", "VALOR CONVÊNIO", 
        "VALOR LIBERADO", "DATA PUBLICAÇÃO", "DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"
    ]
    
    lista_dados = []
    
    try:
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=100000)
        
        for chunk in reader:
            # Padronização rigorosa de colunas e limpeza de espaços
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # Limpa espaços em branco dentro das células de UF e Datas
            if "UF" in chunk.columns:
                chunk["UF"] = chunk["UF"].astype(str).str.strip().str.upper()
            
            # Ajuste de nome Município
            if "MUNICIPIO" in chunk.columns and "NOME MUNICÍPIO" not in chunk.columns:
                chunk = chunk.rename(columns={"MUNICIPIO": "NOME MUNICÍPIO"})

            # 1. FILTRO DE DATA (Busca 2026 na string da Data de Publicação)
            if "DATA PUBLICAÇÃO" in chunk.columns:
                chunk = chunk[chunk["DATA PUBLICAÇÃO"].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. FILTRO DE UF (Apenas se Básico)
            if not acesso_nacional and "UF" in chunk.columns:
                # Compara "SP" do CSV com "SP" do usuário
                chunk = chunk[chunk["UF"] == uf_user]

            if chunk.empty: continue

            # Seleciona colunas que existem no chunk
            cols_atuais = [c for c in colunas_finais if c in chunk.columns]
            lista_dados.append(chunk[cols_atuais].copy())

        df_full = pd.concat(lista_dados, ignore_index=True) if lista_dados else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return

    if df_full.empty:
        st.warning(f"Nenhum registro de 2026 encontrado para a UF: {uf_user}")
        return

    # --- FILTROS DE VIGÊNCIA NO TOPO ---
    st.markdown("### 🔍 Parâmetros de Vigência")
    for col in ["DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"]:
        if col in df_full.columns:
            df_full[col] = pd.to_datetime(df_full[col], dayfirst=True, errors='coerce')

    c1, c2 = st.columns(2)
    with c1:
        data_ini = st.date_input("Início da Vigência a partir de:", value=None)
    with c2:
        data_fim = st.date_input("Final da Vigência até:", value=None)

    if data_ini:
        df_full = df_full[df_full["DATA INÍCIO VIGÊNCIA"] >= pd.Timestamp(data_ini)]
    if data_fim:
        df_full = df_full[df_full["DATA FINAL VIGÊNCIA"] <= pd.Timestamp(data_fim)]

    # --- MÉTRICAS ---
    v_c = df_full["VALOR CONVÊNIO"].apply(limpar_valor).sum() if "VALOR CONVÊNIO" in df_full.columns else 0
    v_l = df_full["VALOR LIBERADO"].apply(limpar_valor).sum() if "VALOR LIBERADO" in df_full.columns else 0
    
    m1, m2 = st.columns(2)
    m1.metric("Total Valor Convênio", f"R$ {v_c:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    m2.metric("Total Valor Liberado", f"R$ {v_l:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    st.divider()

    # --- EXIBIÇÃO ---
    st.write(f"Exibindo **{len(df_full)}** convênios filtrados.")
    
    df_display = df_full.copy()
    for col in ["DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
