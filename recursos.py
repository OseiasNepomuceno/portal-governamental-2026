import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0":
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except:
        return 0.0

@st.cache_data(ttl=600)
def carregar_dados_recursos():
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    if not file_id:
        st.error("ERRO: file_id_convenios não configurado nos Secrets.")
        return pd.DataFrame()
    
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        col_data = next((c for c in df.columns if 'DATA' in c or 'DT' in c), None)
        if col_data:
            df['ANO_FILTRO'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.year
            if df['ANO_FILTRO'].isnull().all():
                df['ANO_FILTRO'] = df[col_data].astype(str).str.extract(r'(\d{4})')
            df['ANO_FILTRO'] = df['ANO_FILTRO'].fillna(0).astype(int).astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        return pd.DataFrame()

def exibir_recursos():
    st.title("📊 Painel de Recursos Governamentais")
    df_base = carregar_dados_recursos()
    
    if df_base.empty:
        st.warning("⚠️ Base de dados não carregada ou vazia.")
        return

    # Mapeamento Dinâmico de Colunas
    col_mun = next((c for c in df_base.columns if 'MUNICI' in c), None)
    col_uf = next((c for c in df_base.columns if c == 'UF' or 'ESTADO' in c), None)
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    col_ano = 'ANO_FILTRO' if 'ANO_FILTRO' in df_base.columns else None

    # Segurança por Plano
    usuario = st.session_state.get('usuario_logado')
    if usuario:
        plano = str(usuario.get('PLANO', 'BRONZE')).upper()
        local = str(usuario.get('local_liberado', '')).upper()

        if "BRONZE" in plano and col_mun:
            cidades = [c.strip().upper() for c in local.split(',')]
            df_base[col_mun] = df_base[col_mun].fillna('').astype(str).str.strip().upper()
            df_base = df_base[df_base[col_mun].isin(cidades)]
        elif "PRATA" in plano and col_uf:
            df_base = df_base[df_base[col_uf].str.strip().upper() == local.strip().upper()]
        elif "OURO" in plano and col_uf:
            estados = [e.strip().upper() for e in local.split(',')]
            df_base = df_base[df_base[col_uf].str.strip().upper().isin(estados)]

    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    # Interface de Filtros
    st.markdown("### Filtros de Busca")
    termo = st.text_input("Palavra-chave:").upper()
    f1, f2 = st.columns(2)
    with f1:
        op_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True) if col_ano else ["Todos"]
        f_ano = st.selectbox("Ano:", op_ano)
    with f2:
        op_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
        f_uf = st.selectbox("UF:", op_uf)

    # Lógica de Filtragem
    df_f = df_base
    if termo:
        mask = df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
        df_f = df_f[mask]
    if f_ano != "Todos":
        df_f = df_f[df_f[col_ano] == f_ano]
    if f_uf != "Todos":
        df_f = df_f[df_f[col_uf] == f_uf]

    # Exibição de Métricas
    st.markdown("---")
    m1, m2 = st.columns(2)
    if 'VALOR_NUM' in df_f.columns and not df_f.empty:
        v_total = df_f['VALOR_NUM'].sum()
        v_fmt = f"R$ {v_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        m1.metric("Volume", v_fmt)
    else:
        m1.metric("Volume", "R$ 0,00")
    m2.metric("Resultados", len(df_f))

    if df_f.empty:
        st.info("📍 Nenhum registro encontrado para estes filtros.")
    else:
        st.dataframe(df_f.head(300), use_container_width=True)

if __name__ == "__main__":
    exibir_recursos()
