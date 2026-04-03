# Arquivo Detetive - Core Essence - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    # 1. VERIFICAÇÃO DO ID (O erro de ontem)
    file_id = st.secrets.get("file_id_convenios")
    if not file_id:
        st.error("❌ Erro: 'file_id_convenios' não configurado nos Secrets.")
        return

    nome_arquivo = "20260320_Convenios.csv"
    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    # 2. DIAGNÓSTICO DO USUÁRIO
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("⚠️ Usuário não identificado. Saia e entre novamente.")
        return

    # Tenta pegar as cidades de várias formas (Rede de segurança)
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]

    # --- SE VIER VAZIO, MOSTRA O DEBUG ---
    if not locais_limpos:
        st.error("❌ O sistema não encontrou cidades no seu cadastro.")
        with st.expander("🔍 CLIQUE AQUI PARA VER O QUE HÁ NO SEU LOGIN"):
            st.write("Dados recebidos pelo sistema:")
            st.json(usuario)
            st.info("Verifique se o nome da coluna na planilha de usuários é exatamente 'local_liberado'.")
        return

    # 3. FILTRAGEM (Lógica Estável)
    lista_pedacos = []
    try:
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)

            if col_mun:
                padrao = '|'.join(locais_limpos)
                chunk_f = chunk[chunk[col_mun].astype(str).str.upper().str.contains(padrao, na=False)].copy()
                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)

        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum dado no CSV para: {locais_limpos}")
        return

    st.success(f"Recursos localizados para {locais_limpos}")
    st.dataframe(df_base, use_container_width=True)
