import streamlit as st
import pandas as pd
import gdown
import os

# Dicionário de tradução para o menu lateral
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
        # Padronização: R$ 1.234,56 -> 1234.56
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: 
        return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos 2026")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando Base de Dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- DADOS DO USUÁRIO ---
    nome_usuario = str(usuario.get('NOME') or usuario.get('USUARIO') or "Consultor").upper()
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper()
    uf_sigla = str(usuario.get('UF_LIBERADA') or usuario.get('UF') or "RJ").strip().upper()
    
    uf_nome_menu = DE_PARA_UF.get(uf_sigla, uf_sigla)
    acesso_nacional = (plano == "PREMIUM" or uf_sigla == "BRASIL")

    # --- MENU LATERAL ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        st.info(f"**LOGIN:** {nome_usuario}")
        if acesso_nacional:
            st.success("✅ **PLANO:** PREMIUM (NACIONAL)")
        else:
            st.warning(f"💼 **PLANO:** BÁSICO (ESTADUAL)")
            st.write(f"📍 **UF LIBERADA:** {uf_nome_menu}")
        st.divider()

    # --- COLUNAS SELECIONADAS (Incluindo Valor Liquidado) ---
    colunas_finais = [
        "Ano da Emenda", 
        "Tipo de Emenda", 
        "Nome do Autor da Emenda", 
        "Localidade de aplicação do recurso", 
        "UF", 
        "Valor Empenhado", 
        "Valor Liquidado", 
        "Valor Pago"
    ]
    
    lista_final = []
    
    try:
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=200000)
        
        for chunk in reader:
            # 1. Filtro de Ano 2026
            if "Ano da Emenda" in chunk.columns:
                chunk = chunk[chunk["Ano da Emenda"].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. Filtro de Localidade / UF
            if not acesso_nacional:
                col_loc = "Localidade de aplicação do recurso"
                col_uf = "UF"
                condicao_loc = chunk[col_loc].astype(str).str.upper().str.contains(uf_sigla, na=False)
                condicao_uf = chunk[col_
