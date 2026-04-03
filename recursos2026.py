# Arquivo Final - Core Essence - Compatibilidade Total - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def normalizar_texto(texto):
    if pd.isna(texto) or texto is None: return ""
    # Remove acentos e espaços extras nas pontas
    nfkd_form = unicodedata.normalize('NFKD', str(texto).strip().upper())
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não identificado.")
        return

    # --- PREPARAÇÃO DOS TERMOS ---
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    # Limpa espaços e acentos dos termos que vêm do seu cadastro de usuários
    termos_busca = [normalizar_texto(c) for c in str(locais_bruto).split(',') if c.strip()]
    
    if not termos_busca:
        st.warning("Nenhum local de busca definido para este usuário.")
        return

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo com engine 'python' e sep=None para ele ADIVINHAR se é vírgula ou ponto-e-vírgula
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Processando bloco {i+1}...")
            
            # Normaliza os nomes das colunas (tira acento de 'Município')
            chunk.columns = [normalizar_texto(c) for c in chunk.columns]
            
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)
            col_uf = next((c for c in chunk.columns if c in ['UF', 'ESTADO', 'SIGLA_UF']), 'UF')

            if col_mun:
                # Criamos a busca 'Contém' (case-insensitive e sem acento)
                # O regex=True permite buscar vários nomes de uma vez
                padrao_regex = '|'.join(termos_busca)
                
                # Criamos uma coluna temporária no chunk para busca sem acentos
                chunk['MUN_TEMP'] = chunk[col_mun].astype(str).apply(normalizar_texto)
                
                # Filtra: Se o nome da cidade no CSV (sem acento) contém algum dos termos buscados
                chunk_f = chunk[chunk['MUN_TEMP'].str.contains(padrao_regex, na=False)].copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro na leitura do arquivo: {e}")
        return

    if df_base.empty:
        st.error(f"❌ Nenhum dado encontrado para: {termos_busca}")
        st.info("Verifique se as cidades no CSV estão escritas de forma similar.")
        return

    # --- LIMPEZA E EXIBIÇÃO ---
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    st.metric("Total Localizado", f"R$ {df_base['VALOR_NUM'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Remove as colunas de controle interno
    cols_display = [c for c in df_base.columns if c not in ['MUN_TEMP', 'VALOR_NUM']]
    st.dataframe(df_base[cols_display], use_container_width=True)
