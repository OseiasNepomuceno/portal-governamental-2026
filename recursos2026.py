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
        # Padronização para conversão float (Remove R$, espaços e ajusta separadores)
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
        
        # Leitura flexível de separadores
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        
        # Padroniza nomes das colunas (Maiúsculo e sem espaços extras)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Criação inteligente do Ano de Filtro baseado em colunas de data
        col_data = next((c for c in df.columns if 'DATA' in c or 'DT' in c), None)
        if col_data:
            df['ANO_FILTRO'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.year
            if df['ANO_FILTRO'].isnull().all():
                df['ANO_FILTRO'] = df[col_data].astype(str).str.extract(r'(\d{4})')
            df['ANO_FILTRO'] = df['ANO_FILTRO'].fillna(0).astype(int).astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar base: {e}")
        return pd.DataFrame()

def exibir_recursos():
    st.title("🛰️ Radar de Recursos (Alta Performance)")
    
    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- MAPEAMENTO DINÂMICO DE COLUNAS (Resiliência contra mudanças no CSV) ---
        col_uf = next((c for c in df_base.columns if c == 'UF' or 'ESTADO' in c), "UF")
        col_mun = next((c for c in df_base.columns if 'MUNICI' in c), "NOME MUNICÍPIO")
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = 'ANO_FILTRO' if 'ANO_FILTRO' in df_base.columns else None

        # --- 1. FILTRO DE SEGURANÇA POR PLANO ---
        usuario = st.session_state.get('usuario_logado')
        
        if usuario:
            plano_user = str(usuario.get('PLANO', 'BRONZE')).upper()
            local_liberado = str(usuario.get('local_liberado', '')).upper()
            
            if "BRONZE" in plano_user:
                cidades_permitidas = [c.strip() for c in local_liberado.split(',')]
                # Garante que a coluna de município exista para filtrar
                if col_mun in df_base.columns:
                    df_base[col_mun] = df_base[col_mun].fillna('').astype(str).str.upper()
                    df_base = df_base[df_base[col_mun].isin(cidades_permitidas)]
                st.sidebar.warning(f"📍 Acesso Bronze: {len(cidades_permitidas)} cidades.")
                
            elif "PRATA" in plano_user:
                if col_uf in df_base.columns:
                    df_base = df_base[df_base[col_uf].str.upper() == local_liberado]
                st.sidebar.info(f"📍 Acesso Prata: Estado {local_liberado}.")
                
            elif "OURO" in plano_user:
                estados_permitidos = [e.strip() for e in local_liberado.split(',')]
                if col_uf in df_base.columns:
                    df_base = df_base[df_base[col_uf].str.upper().isin(estados_permitidos)]
                st.sidebar.info(f"📍 Acesso Ouro: {len(estados_permitidos)} estados.")

        # Conversão de valores financeiros
        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        # --- 2. PAINEL DE FILTROS INTERFACE ---
        st.markdown("### 🔍 Painel de Filtros")
        termo = st.text_input("1. Busca Geral (Favorecido/Objeto):").upper()
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", opcoes_ano)

        with c2:
            opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf in df_base.columns else ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", opcoes_uf)

        with c3
