import streamlit as st
import pandas as pd
import gdown
import os

# Dicionário de conversão (Sigla -> Nome na Base)
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
    uf_sigla = str(usuario.get('UF_LIBERADA') or usuario.get('UF') or "").strip().upper()
    uf_nome_completo = DE_PARA_UF.get(uf_sigla, uf_sigla)
    
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
            st.write(f"📍 **UF:** {uf_nome_completo}")
        st.divider()

    # Termos desejados (Localidade tem prioridade sobre Município)
    termos_desejados = ['ANO', 'TIPO', 'AUTOR', 'LOCALIDADE', 'UF', 'EMPENHADO', 'PAGO']
    lista_final = []
    
    try:
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=150000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # 1. Filtro Ano 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. Filtro UF
            if not acesso_nacional:
                col_uf_base = next((c for c in chunk.columns if c == 'UF'), None)
                if col_uf_base:
                    chunk = chunk[chunk[col_uf_base].astype(str).str.upper() == uf_nome_completo]

            if chunk.empty: continue

            # 3. Seleção de Colunas Limpas
            cols_selecionadas = []
            for t in termos_desejados:
                # Busca a coluna, ignorando códigos e IDs
                encontrada = next((c for c in chunk.columns if t in c 
                                  and 'COD' not in c 
                                  and 'ID' not in c 
                                  and 'IBGE' not in c), None)
                if encontrada:
                    cols_selecionadas.append(encontrada)
            
            # Se a Localidade não foi encontrada, tenta Município como plano B
            if not any('LOCALIDADE' in c for c in cols_selecionadas):
                reserva = next((c for c in chunk.columns if 'MUNICÍPIO' in c and 'COD' not
