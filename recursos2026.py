# Arquivo Atualizado com Filtro de Segurança - 02/04/2026
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
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        if len(df.columns) <= 1:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip')

        df.columns = [str(c).strip().upper() for c in df.columns]
        
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

def exibir_radar():
    st.title("🛰️ Radar de Recursos (Alta Performance)")
    
    # 1. Carrega a base bruta
    df_base = carregar_dados_drive()

    if not df_base.empty:
        # --- [NOVO] FILTRO DE SEGURANÇA POR PLANO ---
        # Pegamos os dados do usuário logado no session_state
        usuario = st.session_state.get('usuario_logado')
        
        if usuario:
            plano_user = str(usuario.get('PLANO', 'BRONZE')).upper()
            local_liberado = str(usuario.get('local_liberado', '')).upper()
            
            col_uf = 'UF'
            col_mun = 'NOME MUNICÍPIO'

            if "BRONZE" in plano_user:
                # Transforma a string "CIDADE1, CIDADE2" em uma lista
                cidades_permitidas = [c.strip() for c in local_liberado.split(',')]
                df_base = df_base[df_base[col_mun].str.upper().isin(cidades_permitidas)]
                st.sidebar.warning(f"📍 Acesso Bronze: {len(cidades_permitidas)} cidades.")
                
            elif "PRATA" in plano_user:
                # Filtra apenas pelo Estado (UF)
                df_base = df_base[df_base[col_uf].str.upper() == local_liberado]
                st.sidebar.info(f"📍 Acesso Prata: Estado {local_liberado}.")
                
            elif "OURO" in plano_user:
                # Filtra por múltiplos estados
                estados_permitidos = [e.strip() for e in local_liberado.split(',')]
                df_base = df_base[df_base[col_uf].str.upper().isin(estados_permitidos)]
                st.sidebar.info(f"📍 Acesso Ouro: {len(estados_permitidos)} estados.")
            
            # Plano DIAMANTE não entra nos IFs e vê a base toda (df_base original)
        
        # --- MAPEAMENTO DE COLUNAS ---
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = 'ANO_FILTRO' if 'ANO_FILTRO' in df_base.columns else None
        col_uf = 'UF' if 'UF' in df_base.columns else None
        col_mun = 'NOME MUNICÍPIO' if 'NOME MUNICÍPIO' in df_base.columns else None

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        st.markdown("### 🔍 Painel de Filtros")
        termo = st.text_input("1. Busca Geral (Favorecido/Objeto):").upper()
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("2. Ano:", opcoes_ano)

        with c2:
            opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
            filtro_uf = st.selectbox("3. Estado (UF):", opcoes_uf)

        with c3:
            if col_mun:
                if filtro_uf != "Todos":
                    cidades_uf = df_base[df_base[col_uf] == filtro_uf][col_mun].dropna().unique().tolist()
                else:
                    cidades_uf = df_base[col_mun].dropna().unique().tolist()
                lista_cidades = ["Todos"] + sorted([str(c) for c in cidades_uf])
            else:
                lista_cidades = ["Todos"]
            filtro_mun = st.selectbox("4. Cidade:", lista_cidades)

        # --- LÓGICA DE FILTRAGEM FINAL ---
        df_f = df_base
        if termo:
            mask = df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_f = df_f[mask]
        if filtro_ano != "Todos":
            df_f = df_f[df_f[col_ano] == filtro_ano]
        if filtro_uf != "Todos":
            df_f = df_f[df_f[col_uf] == filtro_uf]
        if filtro_mun != "Todos":
            df_f = df_f[df_f[col_mun].astype(str) == filtro_mun]

        # --- EXIBIÇÃO ---
        st.markdown("---")
        k1, k2 = st.columns(2)
        if 'VALOR_NUM' in df_f.columns:
            total_soma = df_f['VALOR_NUM'].sum()
            k1.metric("Total Filtrado", f"R$ {total_soma:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        k2.metric("Resultados Encontrados", len(df_f))

        st.write(f"👉 Exibindo resultados filtrados para seu perfil.")
        st.dataframe(df_f.head(500), use_container_width=True)
    else:
        st.info("Aguardando carregamento dos dados...")

if __name__ == "__main__":
    exibir_radar()
