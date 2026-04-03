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

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- LÓGICA DE PERMISSÃO ---
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
        else:
            st.warning(f"💼 **PLANO:** BÁSICO (ESTADUAL)")
            st.write(f"📍 **UF:** {uf_nome_completo}")
        st.divider()

    # --- COLUNAS CONFIGURADAS PARA CONVÊNIOS ---
    colunas_finais = [
        "UF", "NOME MUNICÍPIO", "SITUAÇÃO CONVÊNIO", "OBJETO DO CONVÊNIO", 
        "NOME ÓRGÃO SUPERIOR", "NOME CONVENENTE", "VALOR CONVÊNIO", 
        "VALOR LIBERADO", "DATA PUBLICAÇÃO", "DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"
    ]
    
    lista_dados = []
    
    try:
        # Leitura em blocos para performance
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=150000)
        
        for chunk in reader:
            # Padroniza nomes das colunas
            chunk.columns = [c.upper().strip() for c in chunk.columns]
            
            # Tratamento para variações de nome da coluna Município
            if "MUNICIPIO" in chunk.columns and "NOME MUNICÍPIO" not in chunk.columns:
                chunk = chunk.rename(columns={"MUNICIPIO": "NOME MUNICÍPIO"})

            # 1. Filtro Mandatório: DATA PUBLICAÇÃO (2026)
            if "DATA PUBLICAÇÃO" in chunk.columns:
                chunk = chunk[chunk["DATA PUBLICAÇÃO"].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. Filtro de UF (Apenas se Plano Básico)
            if not acesso_nacional:
                if "UF" in chunk.columns:
                    chunk = chunk[chunk["UF"].astype(str).str.upper() == uf_sigla]

            if chunk.empty: continue

            # 3. Seleção Final de Colunas
            cols_disponiveis = [c for c in colunas_finais if c in chunk.columns]
            lista_dados.append(chunk[cols_disponiveis].copy())

        df_full = pd.concat(lista_dados, ignore_index=True) if lista_dados else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao processar base: {e}")
        return

    if df_full.empty:
        st.warning("Nenhum registro de 2026 encontrado para os critérios aplicados.")
        return

    # --- TRATAMENTO DE DATAS ---
    for col_data in ["DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"]:
        if col_data in df_full.columns:
            df_full[col_data] = pd.to_datetime(df_full[col_data], errors='coerce', dayfirst=True)

    # --- FILTROS DE TOPO (LADO DIREITO) ---
    st.markdown("### 🔍 Parâmetros de Vigência")
    c1, c2 = st.columns(2)
    with c1:
        data_inicio = st.date_input("Vigência Inicial a partir de:", value=None)
    with c2:
        data_fim = st.date_input("Vigência Final até:", value=None)

    # Aplicação dinâmica dos filtros de data
    if data_inicio:
        df_full = df_full[df_full["DATA INÍCIO VIGÊNCIA"] >= pd.Timestamp(data_inicio)]
    if data_fim:
        df_full = df_full[df_full["DATA FINAL VIGÊNCIA"] <= pd.Timestamp(data_fim)]

    # --- MÉTRICAS DE RESUMO ---
    v_conv = df_full["VALOR CONVÊNIO"].apply(limpar_valor).sum() if "VALOR CONVÊNIO" in df_full.columns else 0
    v_lib = df_full["VALOR LIBERADO"].apply(limpar_valor).sum() if "VALOR LIBERADO" in df_full.columns else 0
    
    m1, m2 = st.columns(2)
    m1.metric("Soma Valor Convênio", f"R$ {v_conv:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    m2.metric("Soma Valor Liberado", f"R$ {v_lib:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    st.divider()

    # --- EXIBIÇÃO DA PLANILHA ---
    st.write(f"Exibindo **{len(df_full)}** convênios filtrados.")
    
    # Formatação de datas para visualização amigável
    df_display = df_full.copy()
    for col in ["DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].dt.strftime('%d/%m/%Y')

    st.dataframe(df_display, use_container_width=True, hide_index=True)
