# Arquivo Atualizado - Core Essence - Normalização Total - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# --- FUNÇÃO DE NORMALIZAÇÃO (REMOVE ACENTOS E PADRONIZA) ---
def normalizar_texto(texto):
    if pd.isna(texto) or texto is None:
        return ""
    # Remove acentos (Ex: 'MUNICÍPIO' -> 'MUNICIPIO', 'RIO DE JANEIRO' -> 'RIO DE JANEIRO')
    texto_str = str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto_str)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return texto_sem_acento.strip().upper()

# --- FUNÇÃO DE LIMPEZA MONETÁRIA ---
def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]:
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
        st.error("ERRO: 'file_id_convenios' não configurado nos Secrets.")
        return pd.DataFrame()
    
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Leitura com detecção de separador e codificação latina
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        
        # Padroniza nomes das colunas para MAIÚSCULAS (Município vira MUNICÍPIO)
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
        st.error(f"Erro ao carregar base: {e}")
        return pd.DataFrame()

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    df_raw = carregar_dados_drive()
    if df_raw.empty:
        st.info("Sincronizando com a base de dados do Governo...")
        return

    # --- MAPEAMENTO DE COLUNAS (COM SUPORTE A ACENTOS) ---
    # Busca por 'UF' ou 'ESTADO'
    col_uf = next((c for c in df_raw.columns if c in ['UF', 'ESTADO', 'SIGLA_UF', 'SIGLA UF']), 'UF')
    
    # Busca por 'MUNICÍPIO' (com acento) ou 'MUNICIPIO' (sem acento)
    col_mun = next((c for c in df_raw.columns if 'MUNICI' in c or 'CIDADE' in c), None)
    
    col_valor = next((c for c in df_raw.columns if 'VALOR' in c), None)

    # --- 1. FILTRO DE SEGURANÇA (TRAVA POR PLANO) ---
    usuario = st.session_state.get('usuario_logado')
    df_base = pd.DataFrame()

    if usuario and col_mun:
        plano = str(usuario.get('PLANO', 'BRONZE')).upper()
        local = str(usuario.get('local_liberado', ''))
        
        # Prepara a lista de cidades/estados permitidos (sem acento e maiúsculo)
        permitidos_norm = [normalizar_texto(c) for c in local.split(',') if c.strip()]
        
        if "BRONZE" in plano:
            # Filtra cidades ignorando acento e case
            df_raw['MUN_NORM'] = df_raw[col_mun].apply(normalizar_texto)
            df_base = df_raw[df_raw['MUN_NORM'].isin(permitidos_norm)].copy()
            st.sidebar.success(f"📍 {len(permitidos_norm)} cidades liberadas.")
            
        elif "PRATA" in plano:
            # Filtra estado ignorando acento e case
            df_raw['UF_NORM'] = df_raw[col_uf].apply(normalizar_texto)
            estado_alvo = permitidos_norm[0] if permitidos_norm else ""
            df_base = df_raw[df_raw['UF_NORM'] == estado_alvo].copy()
            st.sidebar.info(f"📍 Estado {estado_alvo} liberado.")
        
        else: # OURO ou ADMIN
            df_base = df_raw.copy()
    else:
        if not col_mun:
            st.error("⚠️ Coluna de Município não localizada no CSV.")
            return

    # Limpeza financeira (apenas nos dados filtrados para evitar erro de 400MB)
    if not df_base.empty:
        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)
        else:
            df_base['VALOR_NUM'] = 0.0

    # --- 2. INTERFACE DE FILTROS ---
    st.markdown("### 🔍 Busca e Filtros")
    termo = st.text_input("Busca por Favorecido ou Objeto:")
    
    c1, c2 = st.columns(2)
    with c1:
        opcoes_ano = ["Todos"] + sorted(df_base['ANO_FILTRO'].unique().tolist(), reverse=True)
        filtro_ano = st.selectbox("Ano:", opcoes_ano)
    with c2:
        # Mostra apenas os Estados que sobraram após o filtro de segurança
        opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().tolist())
        filtro_uf = st.selectbox("Estado (UF):", opcoes_uf)

    # Aplicação dos Filtros de Tela
    df_f = df_base.copy()
    if filtro_ano != "Todos":
        df_f = df_f[df_f['ANO_FILTRO'] == filtro_ano]
    if filtro_uf != "Todos":
        df_f = df_f[df_f[col_uf] == filtro_uf]
    if termo:
        termo_n = normalizar_texto(termo)
        # Busca insensível a acento em todas as colunas
        mask = df_f.astype(str).apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper().str.contains(termo_n)).any(axis=1)
        df_f = df_f[mask]

    # --- 3. EXIBIÇÃO ---
    st.markdown("---")
    if not df_f.empty:
        total = df_f['VALOR_NUM'].sum()
        total_fmt = f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.metric("Total Encontrado", total_fmt)
        
        # Remove colunas auxiliares de sistema
        cols_limpas = [c for c in df_f.columns if '_NORM' not in c and 'VALOR_NUM' != c]
        st.dataframe(df_f[cols_limpas], use_container_width=True)
    else:
        st.metric("Total Encontrado", "R$ 0,00")
        st.info("Nenhum registro encontrado para os critérios selecionados.")
