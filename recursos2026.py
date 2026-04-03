import streamlit as st
import pandas as pd
import gdown
import os

# Dicionário para garantir a conversão de Nome -> Sigla
ESTADO_PARA_SIGLA = {
    'ACRE': 'AC', 'ALAGOAS': 'AL', 'AMAPA': 'AP', 'AMAZONAS': 'AM', 'BAHIA': 'BA',
    'CEARA': 'CE', 'DISTRITO FEDERAL': 'DF', 'ESPIRITO SANTO': 'ES', 'GOIAS': 'GO',
    'MARANHAO': 'MA', 'MT': 'MATO GROSSO', 'MS': 'MATO GROSSO DO SUL', 'MINAS GERAIS': 'MG',
    'PARA': 'PA', 'PARAIBA': 'PB', 'PARANA': 'PR', 'PERNAMBUCO': 'PE', 'PIAUI': 'PI',
    'RIO DE JANEIRO': 'RJ', 'RIO GRANDE DO NORTE': 'RN', 'RIO GRANDE DO SUL': 'RS',
    'RONDONIA': 'RO', 'RORAIMA': 'RR', 'SANTA CATARINA': 'SC', 'SAO PAULO': 'SP',
    'SERGIPE': 'SE', 'TOCANTINS': 'TO'
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
        with st.spinner("Sincronizando Base de Dados Nacional..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    # --- IDENTIFICAÇÃO DO USUÁRIO E PERMISSÕES ---
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper()
    local_cadastrado = str(usuario.get('UF_LIBERADA') or usuario.get('UF') or "").strip().upper()
    
    # Converte para sigla (RJ, SP...) para busca precisa no CSV
    uf_busca = ESTADO_PARA_SIGLA.get(local_cadastrado, local_cadastrado)
    
    # Premium ou "BRASIL" libera todos os estados
    acesso_nacional = (plano == "PREMIUM" or uf_busca == "BRASIL")

    # --- SIDEBAR ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        st.info(f"**LOGIN:** {str(usuario.get('NOME', 'CONSULTOR')).upper()}")
        if acesso_nacional:
            st.success("✅ **PLANO:** PREMIUM (NACIONAL)")
            label_scope = "BRASIL"
        else:
            st.warning(f"💼 **PLANO:** BÁSICO (ESTADUAL)")
            st.write(f"📍 **UF:** {uf_busca}")
            label_scope = uf_busca
        st.divider()

    # --- DEFINIÇÃO DE COLUNAS ---
    colunas_finais = [
        "UF", "NOME MUNICÍPIO", "SITUAÇÃO CONVÊNIO", "OBJETO DO CONVÊNIO", 
        "NOME ÓRGÃO SUPERIOR", "NOME CONVENENTE", "VALOR CONVÊNIO", 
        "VALOR LIBERADO", "DATA PUBLICAÇÃO", "DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"
    ]
    
    lista_dados = []
    
    try:
        # Leitura otimizada (Python engine para lidar com o 'ê' e encoding)
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=150000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # Padronização de nomes (MUNICÍPIO)
            if "MUNICIPIO" in chunk.columns and "NOME MUNICÍPIO" not in chunk.columns:
                chunk = chunk.rename(columns={"MUNICIPIO": "NOME MUNICÍPIO"})

            # 1. Filtro Mandatório: Ano 2026 na Data de Publicação
            if "DATA PUBLICAÇÃO" in chunk.columns:
                chunk = chunk[chunk["DATA PUBLICAÇÃO"].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. Filtro de UF (Apenas se não for Premium)
            if not acesso_nacional and "UF" in chunk.columns:
                chunk["UF"] = chunk["UF"].astype(str).str.strip().str.upper()
                chunk = chunk[chunk["UF"] == uf_busca]

            if chunk.empty: continue

            # Seleção segura de colunas
            cols_atuais = [c for c in colunas_finais if c in chunk.columns]
            lista_dados.append(chunk[cols_atuais].copy())

        df_full = pd.concat(lista_dados, ignore_index=True) if lista_dados else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro técnico no processamento: {e}")
        return

    if df_full.empty:
        st.warning(f"Nenhum registro de 2026 encontrado para: {label_scope}")
        return

    # --- FILTROS DE TOPO (MESMA EXPERIÊNCIA PARA AMBOS OS PLANOS) ---
    st.markdown("### 🔍 Parâmetros de Vigência")
    for col in ["DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"]:
        if col in df_full.columns:
            df_full[col] = pd.to_datetime(df_full[col], dayfirst=True, errors='coerce')

    c1, c2 = st.columns(2)
    with c1:
        data_ini = st.date_input("Início da Vigência a partir de:", value=None)
    with c2:
        data_fim = st.date_input("Final da Vigência até:", value=None)

    # Filtros dinâmicos
    if data_ini:
        df_full = df_full[df_full["DATA INÍCIO VIGÊNCIA"] >= pd.Timestamp(data_ini)]
    if data_fim:
        df_full = df_full[df_full["DATA FINAL VIGÊNCIA"] <= pd.Timestamp(data_fim)]

    # --- MÉTRICAS ---
    v_c = df_full["VALOR CONVÊNIO"].apply(limpar_valor).sum() if "VALOR CONVÊNIO" in df_full.columns else 0
    v_l = df_full["VALOR LIBERADO"].apply(limpar_valor).sum() if "VALOR LIBERADO" in df_full.columns else 0
    
    m1, m2 = st.columns(2)
    m1.metric("Soma Valor Convênio", f"R$ {v_c:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    m2.metric("Soma Valor Liberado", f"R$ {v_l:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    st.divider()

    # --- EXIBIÇÃO DA PLANILHA ---
    st.write(f"Exibindo **{len(df_full)}** registros encontrados em **{label_scope}**.")
    
    df_display = df_full.copy()
    for col in ["DATA INÍCIO VIGÊNCIA", "DATA FINAL VIGÊNCIA"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
