import streamlit as st
import pandas as pd
import gdown
import os

@st.cache_data(ttl=60)
def carregar_licencas():
    # ID da planilha ID_LICENÇAS (pegue do seu Drive e coloque no Secrets)
    file_id = st.secrets.get("file_id_licencas")
    nome_arquivo = "licencas.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    
    try:
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        gdown.download(url, nome_arquivo, quiet=True)
        
        # Lê a aba 'usuario' conforme os dados detectados 
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        return df
    except Exception as e:
        st.error(f"Erro ao acessar ID_LICENÇAS: {e}")
        return pd.DataFrame()

def exibir_gestao():
    st.title("⚙️ Gestão Administrativa de Licenças")
    st.caption("Controle de Acessos - Core Essence")

    df_usuarios = carregar_licencas()

    if not df_usuarios.empty:
        # Indicadores rápidos
        total = len(df_usuarios)
        ativos = len(df_usuarios[df_usuarios['status'].str.lower() == 'ativo'])
        expirados = len(df_usuarios[df_usuarios['status'].str.lower() == 'expirado'])

        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Usuários", total)
        c2.metric("Ativos ✅", ativos)
        c3.metric("Expirados ⚠️", expirados)

        st.divider()

        # Filtro de Busca
        busca = st.text_input("Pesquisar usuário:").lower()
        if busca:
            df_usuarios = df_usuarios[df_usuarios['usuario'].str.lower().contains(busca)]

        # Tabela de Controle
        st.subheader("📋 Lista de Usuários e Status")
        
        # Estilização para destacar quem está expirado
        def color_status(val):
            color = '#ff4b4b' if val == 'expirado' else '#28a745'
            return f'color: {color}; font-weight: bold'

    # --- TABELA DE CONTROLE ---
        # Removi o st.subheader daqui para não duplicar com o portal.py
        
        def color_status(val):
            v = str(val).lower().strip()
            if v == 'expirado':
                return 'color: #ff4b4b; font-weight: bold;'
            if v == 'ativo':
                return 'color: #28a745; font-weight: bold;'
            return ''

        try:
            # Tenta o comando novo (Pandas 2.0+)
            st.dataframe(df_usuarios.style.map(color_status, subset=['status']), use_container_width=True)
        except:
            # Tenta o comando antigo se o servidor estiver desatualizado
            try:
                st.dataframe(df_usuarios.style.applymap(color_status, subset=['status']), use_container_width=True)
            except:
                # Se tudo falhar, mostra a tabela pura
                st.dataframe(df_usuarios, use_container_width=True)
