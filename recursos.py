# Arquivo: recursos.py - Atualizado com Trava de Segurança em 03/04/2026
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
def carregar_dados_recursos():
    # Certifique-se que o segredo 'file_id_convenios' está no Streamlit Cloud
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    if not file_id:
        st.error("ERRO: file_id_convenios não configurado nos Secrets.")
        return pd.DataFrame()

    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if not os.path.exists(nome_arquivo):
            gdown.download(url, nome_arquivo, quiet=True)
        
        # Tenta carregar com diferentes separadores
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
        st.error(f"Erro ao processar base de Recursos: {e}")
        return pd.DataFrame()

def exibir_recursos():
    st.title("📊 Painel de Recursos Governamentais")
    
    # Carrega a base
    df_base = carregar_dados_recursos()

    if not df_base.empty:
        # --- FILTRO DE SEGURANÇA POR PLANO ---
        usuario = st.session_state.get('usuario_logado')
        
        if usuario:
            plano_user = str(usuario.get('PLANO', 'BRONZE')).upper()
            local_liberado = str(usuario.get('local_liberado', '')).upper()
            
            col_uf = 'UF'
            col_mun = 'NOME MUNICÍPIO'

            # Aplicando restrições de visibilidade conforme o plano
            if "BRONZE" in plano_user and col_mun in df_base.columns:
                cidades_permitidas = [c.strip().upper() for c in local_liberado.split(',')]
                df_base = df_base[df_base[col_mun].str.upper().isin(cidades_permitidas)]
                
            elif "PRATA" in plano_user and col_uf in df_base.columns:
                df_base = df_base[df_base[col_uf].str.upper() == local_liberado]
                
            elif "OURO" in plano_user and col_uf in df_base.columns:
                estados_permitidos = [e.strip().upper() for e in local_liberado.split(',')]
                df_base = df_base[df_base[col_uf].str.upper().isin(estados_permitidos)]

        # --- MAPEAMENTO E FILTROS INTERATIVOS ---
        col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
        col_ano = 'ANO_FILTRO' if 'ANO_FILTRO' in df_base.columns else None
        col_uf = 'UF' if 'UF' in df_base.columns else None
        col_mun = 'NOME MUNICÍPIO' if 'NOME MUNICÍPIO' in df_base.columns else None

        if col_valor:
            df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

        st.markdown("### 🔍 Filtros de Análise")
        termo = st.text_input("Busca por Palavra-Chave (Favorecido ou Objeto):").upper()
        
        f1, f2 = st.columns(2)
        with f1:
            opcoes_ano = ["Todos"] + sorted(df_base[col_ano].unique().tolist(), reverse=True) if col_ano else ["Todos"]
            filtro_ano = st.selectbox("Filtrar Ano:", opcoes_ano, key="rec_ano")
        with f2:
            opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().astype(str).tolist()) if col_uf else ["Todos"]
            filtro_uf = st.selectbox("Filtrar Estado:", opcoes_uf, key="rec_uf")

        # Lógica de Filtragem
        df_f = df_base
        if termo:
            mask = df_f.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
            df_f = df_f[mask]
        if filtro_ano != "Todos":
            df_f = df_f[df_f[col_ano] == filtro_ano]
        if filtro_uf != "Todos":
            df_f = df_f[df_f[col_uf] == filtro_uf]

        # --- MÉTRICAS COM AJUSTE DE SEGURANÇA (EVITA TELA BRANCA) ---
        st.markdown("---")
        m1, m2 = st.columns(2)
        
        if 'VALOR_NUM' in df_f.columns and not df_f.empty:
            total = df_f['VALOR_NUM'].sum()
            valor_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            m1.metric("Volume de Recursos", valor_formatado)
        else:
            m1.metric("Volume de Recursos", "R$ 0,00")
            
        m2.metric("Resultados Encontrados", len(df_f))

        # --- EXIBIÇÃO DA TABELA ---
        if df_f.empty:
            st.warning("📍 Nenhum dado encontrado para os filtros selecionados ou para sua região liberada.")
        else:
            st.dataframe(df_f.head(300), use_container_width=True)
            
    else:
        st.warning("⚠️ Não foi possível carregar os dados de Recursos. Verifique sua conexão ou permissões.")

# Se rodar este arquivo isoladamente (para testes)
if __name__ == "__main__":
    if 'usuario_logado' not in st.session_state:
        st.session_state['usuario_logado'] = {'PLANO': 'DIAMANTE', 'local_liberado': 'TODOS'}
    exibir_recursos()
