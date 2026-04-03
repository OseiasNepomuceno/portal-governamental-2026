import streamlit as st
import pandas as pd
import gdown
import os

# Tradução para interface e filtros
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
    # NOME AJUSTADO COM ACENTO CONFORME O DRIVE
    nome_arquivo = "20260320_Convênios.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando Base de Recursos do Drive..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- LÓGICA DE USUÁRIO ---
    nome_usuario = str(usuario.get('NOME') or usuario.get('USUARIO') or "Consultor").upper()
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper()
    uf_sigla = str(usuario.get('UF_LIBERADA') or usuario.get('UF') or "RJ").strip().upper()
    
    uf_nome_completo = DE_PARA_UF.get(uf_sigla, uf_sigla)
    acesso_nacional = (plano == "PREMIUM" or uf_sigla == "BRASIL")

    # --- SIDEBAR ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        st.info(f"**LOGIN:** {nome_usuario}")
        if acesso_nacional:
            st.success("✅ **PLANO:** PREMIUM (NACIONAL)")
            label_scope = "BRASIL"
        else:
            st.warning(f"💼 **PLANO:** BÁSICO (ESTADUAL)")
            st.write(f"📍 **UF:** {uf_nome_completo}")
            label_scope = uf_nome_completo
        st.divider()

    # Colunas esperadas na planilha de recursos
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
        # Leitura com engine python para suportar acentuação no nome do arquivo e encoding latin1
        reader = pd.read_csv(
            nome_arquivo, 
            sep=None, 
            engine='python', 
            encoding='latin1', 
            on_bad_lines='skip', 
            chunksize=150000
        )
        
        for chunk in reader:
            # 1. Filtro Ano 2026
            if "Ano da Emenda" in chunk.columns:
                chunk = chunk[chunk["Ano da Emenda"].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. Filtro Localidade (Plano Básico)
            if not acesso_nacional:
                col_loc = "Localidade de aplicação do recurso"
                col_uf = "UF"
                cond_loc = chunk[col_loc].astype(str).str.upper().str.contains(uf_sigla, na=False)
                cond_uf = chunk[col_uf].astype(str).str.upper() == uf_nome_completo
                chunk = chunk[cond_loc | cond_uf]

            if chunk.empty: continue

            # 3. Seleção das Colunas
            cols_atuais = [c for c in colunas_finais if c in chunk.columns]
            lista_final.append(chunk[cols_atuais].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro na leitura do arquivo '{nome_arquivo}': {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum registro de 2026 encontrado para {label_scope}.")
        return

    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    
    v_e = df_base["Valor Empenhado"].apply(limpar_valor).sum() if "Valor Empenhado" in df_base.columns else 0
    v_l = df_base["Valor Liquidado"].apply(limpar_valor).sum() if "Valor Liquidado" in df_base.columns else 0
    v_p = df_base["Valor Pago"].apply(limpar_valor).sum() if "Valor Pago" in df_base.columns else 0
    
    m1.metric("Total Empenhado", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    m2.metric("Total Liquidado", f"R$ {v_l:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    m3.metric("Total Pago", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    st.write(f"Exibindo **{len(df_base)}** registros encontrados.")
    st.dataframe(df_base, use_container_width=True)
