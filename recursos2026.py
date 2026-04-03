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

    # Nomes flexíveis para encontrar as colunas mesmo com acentos
    alvos = ['ANO', 'TIPO', 'AUTOR', 'MUNICÍPIO', 'MUNICIPIO', 'UF', 'EMPENHADO', 'PAGO']
    lista_final = []
    
    try:
        # Aumentei o chunksize para garantir que ele pegue mais dados por vez
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=150000)
        
        for chunk in reader:
            # Mantém os nomes originais para busca, mas cria uma versão upper para comparar
            cols_originais = chunk.columns
            cols_upper = [str(c).upper().strip() for c in cols_originais]
            chunk.columns = cols_upper # Padroniza temporariamente
            
            # 1. FILTRO ANO 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. FILTRO POR UF (RIGOROSO)
            if not acesso_nacional:
                # Busca a coluna UF exata
                col_uf_base = next((c for c in chunk.columns if c == 'UF'), None)
                if col_uf_base:
                    chunk = chunk[chunk[col_uf_base].astype(str).str.upper() == uf_nome_completo]

            if chunk.empty: continue

            # 3. SELEÇÃO DE COLUNAS (Incluindo 'Município' com acento)
            cols_para_exibir = []
            for item in ['ANO', 'TIPO', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'PAGO']:
                # Busca qualquer coluna que contenha a palavra chave (ex: encontra 'Município' se buscar 'MUNICÍPIO')
                encontrada = next((c for c in chunk.columns if item in c and 'COD' not in c), None)
                if encontrada:
                    cols_para_exibir.append(encontrada)
            
            if cols_para_exibir:
                lista_final.append(chunk[list(dict.fromkeys(cols_para_exibir))].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum dado encontrado para: {uf_nome_completo}")
        return

    # --- MÉTRICAS E TABELA ---
    # Identifica colunas financeiras para soma
    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)
    label = "BRASIL" if acesso_nacional else uf_nome_completo
    
    if col_e:
        total_e = df_base[col_e].apply(limpar_valor).sum()
        m1.metric(f"Total Empenhado ({label})", f"R$ {total_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if col_p:
        total_p = df_base[col_p].apply(limpar_valor).sum()
        m2.metric(f"Total Pago ({label})", f"R$ {total_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    st.dataframe(df_base, use_container_width=True)
