# Arquivo Atualizado - Correção de Memória e Trava de Segurança - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# --- FUNÇÃO DE NORMALIZAÇÃO ---
def normalizar_texto(texto):
    if pd.isna(texto) or texto is None:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).strip().upper()

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
        st.error("ERRO: 'file_id_convenios' não configurado.")
        return pd.DataFrame()
    
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Lendo apenas as colunas necessárias para economizar memória (OPCIONAL, mas ajuda)
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
        st.error(f"Erro ao carregar base: {e}")
        return pd.DataFrame()

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    # 1. Carrega a base bruta
    df_raw = carregar_dados_drive()
    if df_raw.empty:
        st.warning("Aguardando carregamento da base...")
        return

    # --- MAPEAMENTO DE COLUNAS ---
    col_uf = next((c for c in df_raw.columns if c == 'UF' or 'ESTADO' in c), "UF")
    col_mun = next((c for c in df_raw.columns if 'MUNICI' in c or 'CIDADE' in c), "MUNICIPIO")
    col_valor = next((c for c in df_raw.columns if 'VALOR' in c), None)

    # --- 2. APLICAÇÃO IMEDIATA DA TRAVA DE SEGURANÇA (ECONOMIA DE MEMÓRIA) ---
    usuario = st.session_state.get('usuario_logado')
    df_base = pd.DataFrame() # Começa vazio por segurança

    if usuario:
        plano = str(usuario.get('PLANO', 'BRONZE')).upper()
        local = str(usuario.get('local_liberado', ''))
        
        if "BRONZE" in plano:
            cidades_permitidas = [normalizar_texto(c) for c in local.split(',') if c.strip()]
            # Criamos uma coluna temporária para filtrar e já descartamos a bruta para economizar RAM
            df_raw['MUN_NORM'] = df_raw[col_mun].apply(normalizar_texto)
            df_base = df_raw[df_raw['MUN_NORM'].isin(cidades_permitidas)].copy()
            st.sidebar.warning(f"📍 Plano Bronze: {len(cidades_permitidas)} cidades.")
            
        elif "PRATA" in plano:
            estado_alvo = normalizar_texto(local)
            df_raw['UF_NORM'] = df_raw[col_uf].apply(normalizar_texto)
            df_base = df_raw[df_raw['UF_NORM'] == estado_alvo].copy()
            st.sidebar.info(f"📍 Plano Prata: Estado {estado_alvo}.")
        
        else: # Ouro ou Admin
            df_base = df_raw.copy()

    # Se após a trava o DF estiver vazio, paramos aqui
    if df_base.empty:
        st.info("ℹ️ Nenhum dado disponível para sua licença nesta base.")
        return

    # Limpeza financeira (só no que sobrou da trava)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    # --- 3. INTERFACE DE FILTROS DINÂMICOS (TRAVADOS PELO PLANO) ---
    st.markdown("### 🔍 Busca e Filtros")
    termo = st.text_input("Busca por Favorecido ou Objeto:")
    
    c1, c2 = st.columns(2)
    with c1:
        # Só mostra anos que existem nos dados liberados
        opcoes_ano = ["Todos"] + sorted(df_base['ANO_FILTRO'].unique().tolist(), reverse=True)
        filtro_ano = st.selectbox("Ano:", opcoes_ano)
    with c2:
        # Só mostra estados que existem nos dados liberados (Para Gláucia aparecerá só RJ)
        opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().tolist())
        filtro_uf = st.selectbox("Estado (UF):", opcoes_uf)

    # Filtragem Final
    df_f = df_base.copy()
    if filtro_ano != "Todos":
        df_f = df_f[df_f['ANO_FILTRO'] == filtro_ano]
    if filtro_uf != "Todos":
        df_f = df_f[df_f[col_uf] == filtro_uf]
    if termo:
        termo_norm = normalizar_texto(termo)
        mask = df_f.astype(str).apply(lambda x: x.str.upper().contains(termo_norm)).any(axis=1)
        df_f = df_f[mask]

    # --- 4. EXIBIÇÃO ---
    st.markdown("---")
    if not df_f.empty:
        total = df_f['VALOR_NUM'].sum()
        st.metric("Total Encontrado", f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Remove colunas auxiliares antes de mostrar
        cols_limpas = [c for c in df_f.columns if '_NORM' not in c and 'VALOR_NUM' != c]
        st.dataframe(df_f[cols_limpas], use_container_width=True)
    else:
        st.metric("Total Encontrado", "R$ 0,00")
        st.info("Nenhum registro encontrado para esses filtros.")
