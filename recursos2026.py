# Arquivo Restaurado - Core Essence - Versão Estável de Ontem - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: return 0.0
    try:
        # A limpeza simples que funcionava ontem
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    # 1. DOWNLOAD (O mesmo método de ontem)
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    # 2. LOGIN E PERMISSÕES (Recuperando do Session State)
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.warning("Efetue o login para acessar.")
        return

    # Pegamos os locais exatamente como estão na sua planilha (Com acento agora, como você mudou)
    locais_liberados = str(usuario.get('local_liberado', '')).upper().split(',')
    locais_limpos = [c.strip() for c in locais_liberados if c.strip()]
    
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em blocos de 60 mil linhas (Única trava de segurança necessária)
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Filtrando dados... Bloco {i+1}")
            
            # Padroniza as colunas para maiúsculo (como ontem)
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # Identifica a coluna Município
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)

            if col_mun:
                # LÓGICA DE ONTEM: Busca parcial por "Contém"
                # O '|'.join cria um filtro 'OU' (NITERÓI ou RIO DE JANEIRO ou PETRÓPOLIS)
                if plano in ["BRONZE", "PRATA"]:
                    padrao_busca = '|'.join(locais_limpos)
                    # Verifica se o texto da planilha está contido no texto do CSV
                    chunk_f = chunk[chunk[col_mun].astype(str).str.upper().str.contains(padrao_busca, na=False)].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)

        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return

    # 3. EXIBIÇÃO
    if df_base.empty:
        st.error(f"❌ Nenhum dado encontrado para: {locais_limpos}")
        st.info("Verifique se as cidades na planilha de usuários estão idênticas às do CSV.")
        return

    # Tratamento de valores
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    # Dashboard e Tabela
    total = df_base['VALOR_NUM'].sum() if 'VALOR_NUM' in df_base.columns else 0
    st.metric("Soma Total dos Recursos", f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.dataframe(df_base.drop(columns=['VALOR_NUM'], errors='ignore'), use_container_width=True)
