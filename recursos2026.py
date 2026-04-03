# Arquivo Atualizado - Normalização de Acentos e Case - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# --- FUNÇÃO DE NORMALIZAÇÃO (REMOVE ACENTOS E ESPAÇOS) ---
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    # Remove acentos, espaços extras e coloca em MAIÚSCULO
    nfkd_form = unicodedata.normalize('NFKD', str(texto))
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return texto_sem_acento.strip().upper()

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

    # --- MAPEAMENTO DE COLUNAS ---
    col_uf = next((c for c in df_base.columns if c == 'UF' or 'ESTADO' in c), "UF")
    col_mun = next((c for c in df_base.columns if 'MUNICI' in c or 'CIDADE' in c), None)
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    col_ano = 'ANO_FILTRO'

    # --- 1. FILTRO DE SEGURANÇA POR PLANO COM NORMALIZAÇÃO ---
    usuario = st.session_state.get('usuario_logado')
    
    if usuario and col_mun:
        plano_user = str(usuario.get('PLANO', 'BRONZE')).upper()
        local_liberado = str(usuario.get('local_liberado', ''))
        
        # Normaliza a lista de cidades da planilha (Ex: "Niterói" vira "NITEROI")
        cidades_permitidas = [normalizar_texto(c) for c in local_liberado.split(',') if c.strip()]
        
        if "BRONZE" in plano_user:
            # Normaliza a coluna do CSV para bater com a lista
            df_base['MUN_NORMALIZADO'] = df_base[col_mun].apply(normalizar_texto)
            df_base = df_base[df_base['MUN_NORMALIZADO'].isin(cidades_permitidas)]
            
            st.sidebar.warning(f"📍 Acesso Bronze: {len(cidades_permitidas)} cidades.")
            st.sidebar.write(f"Cidades Ativas: {', '.join(cidades_permitidas)}")
            
        elif "PRATA" in plano_user:
            estado_alvo = normalizar_texto(local_liberado)
            df_base['UF_NORMALIZADA'] = df_base[col_uf].apply(normalizar_texto)
            df_base = df_base[df_base['UF_NORMALIZADA'] == estado_alvo]
            st.sidebar.info(f"📍 Acesso Prata: Estado {estado_alvo}.")
            
        elif "OURO" in plano_user:
            estados_permitidos = [normalizar_texto(e) for e in local_liberado.split(',') if e.strip()]
            df_base['UF_NORMALIZADA'] = df_base[col_uf].apply(normalizar_texto)
            df_base = df_base[df_base['UF_NORMALIZADA'].isin(estados_permitidos)]
            st.sidebar.info(f"📍 Acesso Ouro: {len(estados_permitidos)} estados.")

    # Conversão de valores financeiros
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)
    else:
        df_base['VALOR_NUM'] = 0.0

    # --- 2. INTERFACE DE FILTROS ---
    st.markdown("### 🔍 Busca e Filtros")
    termo = st.text_input("Busca por Favorecido ou Objeto:")
    
    # Normaliza o termo de busca para a pesquisa ser ampla
    termo_norm = normalizar_texto(termo)
    
    c1, c2 = st.columns(2)
    with c1:
        opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True)
        filtro_ano = st.selectbox("Ano:", opcoes_ano)
    with c2:
        opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist())
        filtro_uf = st.selectbox("Estado (UF):", opcoes
