# Arquivo Atualizado com Filtro de Segurança e Resiliência de Colunas - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

# --- FUNÇÃO DE LIMPEZA MONETÁRIA ---
def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0":
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except:
        return 0.0

@st.cache_data(ttl=600)
def carregar_dados_drive():
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    if not file_id:
        st.error("ERRO: 'file_id_convenios' não configurado.")
        return pd.DataFrame()
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Criar Ano de Filtro
        col_data = next((c for c in df.columns if 'DATA' in c or 'DT' in c), None)
        if col_data:
            df['ANO_FILTRO'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.year
            df['ANO_FILTRO'] = df['ANO_FILTRO'].fillna(0).astype(int).astype(str)
        else:
            df['ANO_FILTRO'] = "2026"
        return df
    except Exception as e:
        st.error(f"Erro ao processar base: {e}")
        return pd.DataFrame()

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    df_base = carregar_dados_drive()

    if df_base.empty:
        st.warning("A base de dados está vazia ou não foi carregada.")
        return

    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    # Busca por UF
    col_uf = next((c for c in df_base.columns if c == 'UF' or 'ESTADO' in c), "UF")
    
    # Busca por Município (Tenta várias combinações comuns em portais governamentais)
    col_mun = next((c for c in df_base.columns if any(p in c for p in ['MUNICI', 'CIDADE', 'LOCALIDADE', 'BENEFICIARIO'])), None)
    
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    col_ano = 'ANO_FILTRO'

    # --- 1. FILTRO DE SEGURANÇA POR PLANO ---
    usuario = st.session_state.get('usuario_logado')
    
    if usuario and col_mun:
        plano_user = str(usuario.get('PLANO', 'BRONZE')).upper()
        local_liberado = str(usuario.get('local_liberado', '')).upper()
        
        # Limpa e separa a lista de cidades da planilha
        cidades_permitidas = [c.strip() for c in local_liberado.split(',') if c.strip()]
        
        if "BRONZE" in plano_user:
            # Garante que a coluna do CSV seja tratada como string antes do strip/upper
            df_base[col_mun] = df_base[col_mun].astype(str).str.strip().upper()
            df_base = df_base[df_base[col_mun].isin(cidades_permitidas)]
            st.sidebar.warning(f"📍 Acesso Bronze: {len(cidades_permitidas)} cidades.")
            
        elif "PRATA" in plano_user:
            if col_uf in df_base.columns:
                df_base = df_base[df_base[col_uf].astype(str).str.strip().upper() == local_liberado.strip()]
            st.sidebar.info(f"📍 Acesso Prata: Estado {local_liberado}.")
            
        elif "OURO" in plano_user:
            estados_permitidos = [e.strip() for e in local_liberado.split(',') if e.strip()]
            if col_uf in df_base.columns:
                df_base = df_base[df_base[col_uf].astype(str).str.strip().upper().isin(estados_permitidos)]
            st.sidebar.info(f"📍 Acesso Ouro: {len(estados_permitidos)} estados.")
    else:
        if not col_mun:
            st.error("⚠️ Coluna de Município não encontrada no CSV. Verifique os nomes das colunas.")

    # Conversão de valores financeiros
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)
    else:
        df_base['VALOR_NUM'] = 0.0

    # --- 2. INTERFACE DE FILTROS ---
    st.markdown("### 🔍 Busca e Filtros")
    termo = st.text_input("Busca por Favorecido ou Objeto:").upper()
    
    c1, c2 = st.columns(2)
    with c1:
        opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True)
        filtro_ano = st.selectbox("Ano:", opcoes_ano)
    with c2:
        opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist())
        filtro_uf = st.selectbox("Estado (UF):", opcoes_uf)

    # Aplicação dos Filtros
    df_f = df_base.copy()
    if filtro_ano != "Todos":
        df_f = df_f[df_f[col_ano] == filtro_ano]
    if filtro_uf != "Todos":
        df_f = df_f[df_f[col_uf] == filtro_uf]
    if termo:
        mask = df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
        df_f = df_f[mask]

    # --- 3. EXIBIÇÃO ---
    st.markdown("---")
    if not df_f.empty:
        total_soma = df_f['VALOR_NUM'].sum()
        total_formatado = f"R$ {total_soma:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.metric("Total Encontrado", total_formatado)
        st.dataframe(df_f, use_container_width=True)
    else:
        st.metric("Total Encontrado", "R$ 0,00")
        st.warning("⚠️ Nenhum registro encontrado.")
