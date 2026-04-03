import streamlit as st
import pandas as pd
import gdown
import os

# Dicionário de tradução exata para a coluna "UF" da sua base
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
    
    # Traduz para o nome por extenso que está na sua base (ex: RIO DE JANEIRO)
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
            st.write(f"📍 **UF LIBERADA:** {uf_nome_completo}")
        st.divider()

    # --- DEFINIÇÃO DAS COLUNAS EXATAS (Baseado no seu Diagnóstico) ---
    colunas_finais = [
        "Ano da Emenda", 
        "Tipo de Emenda", 
        "Nome do Autor da Emenda", 
        "Localidade de aplicação do recurso", 
        "UF", 
        "Valor Empenhado", 
        "Valor Pago"
    ]
    
    lista_final = []
    
    try:
        # Leitura por blocos para não travar
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=150000)
        
        for chunk in reader:
            # 1. Filtro de Ano (2026)
            if "Ano da Emenda" in chunk.columns:
                chunk = chunk[chunk["Ano da Emenda"].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. Filtro de UF (Apenas se for Plano Básico)
            if not acesso_nacional:
                if "UF" in chunk.columns:
                    chunk = chunk[chunk["UF"].astype(str).str.upper() == uf_nome_completo]

            if chunk.empty: continue

            # 3. Seleção das colunas exatas que você pediu (Sem códigos)
            # Verificamos se as colunas existem antes de selecionar
            cols_existentes = [c for c in colunas_finais if c in chunk.columns]
            lista_final.append(chunk[cols_existentes].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum dado encontrado para {uf_nome_completo} em 2026.")
        return

    # --- MÉTRICAS ---
    # Usamos os nomes exatos do seu diagnóstico para a soma
    m1, m2 = st.columns(2)
    label_local = "BRASIL" if acesso_nacional else uf_nome_completo
    
    if "Valor Empenhado" in df_base.columns:
        v_e = df_base["Valor Empenhado"].apply(limpar_valor).sum()
        m1.metric(f"Total Empenhado ({label_local})", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    if "Valor Pago" in df_base.columns:
        v_p = df_base["Valor Pago"].apply(limpar_valor).sum()
        m2.metric(f"Total Pago ({label_local})", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    
    # Exibe a planilha final com os títulos corretos
    st.dataframe(df_base, use_container_width=True)
