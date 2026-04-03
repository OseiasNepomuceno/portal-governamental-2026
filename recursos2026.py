import streamlit as st
import pandas as pd
import gdown
import os

# Dicionário de conversão de Sigla para Nome Completo (Padrão da sua Base)
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
        with st.spinner("Sincronizando Base de Dados Nacional..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- LÓGICA DE LOGIN E PLANO ---
    nome_usuario = str(usuario.get('NOME') or usuario.get('USUARIO') or "Consultor").upper()
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper()
    uf_sigla = str(usuario.get('UF_LIBERADA') or "").strip().upper()

    # Tradução da Sigla para o Nome Completo (ex: RJ -> RIO DE JANEIRO)
    uf_nome_completo = DE_PARA_UF.get(uf_sigla, uf_sigla)
    
    acesso_nacional = (plano == "PREMIUM" or uf_sigla == "BRASIL")

    # --- MENU LATERAL (ESQUERDO) ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        # Exibe o Nome do Usuário Logado
        st.info(f"**LOGIN:** {nome_usuario}")
        
        if acesso_nacional:
            st.success("✅ **PLANO:** PREMIUM (NACIONAL)")
        else:
            st.warning(f"💼 **PLANO:** BÁSICO (ESTADUAL)")
            st.write(f"📍 **JURISDIÇÃO:** {uf_nome_completo}")
        st.divider()

    # Colunas da tabela
    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']
    lista_final = []
    
    try:
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=100000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # 1. FILTRO ANO 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. FILTRO DE ACESSO (CORRIGIDO PARA NOME COMPLETO)
            if not acesso_nacional:
                col_uf_csv = next((c for c in chunk.columns if c == 'UF' or ('UF' in c and 'COD' not in c)), None)
                if col_uf_csv:
                    # Agora ele filtra por "RIO DE JANEIRO" em vez de "RJ"
                    chunk = chunk[chunk[col_uf_csv].astype(str).str.upper() == uf_nome_completo]

            if chunk.empty: continue

            # 3. SELEÇÃO DE COLUNAS
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c), None)
                if encontrada: cols_ok.append(encontrada)
            
            if cols_ok:
                lista_final.append(chunk[list(dict.fromkeys(cols_ok))].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return

    # --- EXIBIÇÃO NO DASHBOARD ---
    if df_base.empty:
        st.warning(f"Nenhum dado de 2026 encontrado para: {uf_nome_completo}")
        return

    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)
    label_regiao = "BRASIL" if acesso_nacional else uf_nome_completo
    
    if col_e:
        v_e = df_base[col_e].apply(limpar_valor).sum()
        m1.metric(f"Total Empenhado ({label_regiao})", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if col_p:
        v_p = df_base[col_p].apply(limpar_valor).sum()
        m2.metric(f"Total Pago ({label_regiao})", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    st.dataframe(df_base, use_container_width=True)
