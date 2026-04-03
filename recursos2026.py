# Arquivo Finalizado - Core Essence - Resiliência e Performance Total - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# --- MAPEAMENTO DE SIGLAS PARA GARANTIR FILTRAGEM DE ESTADO ---
MAPEAMENTO_UF = {
    'RIO DE JANEIRO': 'RJ', 'SAO PAULO': 'SP', 'MINAS GERAIS': 'MG', 'ESPIRITO SANTO': 'ES',
    'PARANA': 'PR', 'SANTA CATARINA': 'SC', 'RIO GRANDE DO SUL': 'RS', 'BAHIA': 'BA',
    'MATO GROSSO': 'MT', 'MATO GROSSO DO SUL': 'MS', 'GOIAS': 'GO', 'DISTRITO FEDERAL': 'DF'
}

# --- FUNÇÃO DE NORMALIZAÇÃO (REMOVE ACENTOS E PADRONIZA) ---
def normalizar_texto(texto):
    if pd.isna(texto) or texto is None:
        return ""
    # Transforma 'MUNICÍPIO' em 'MUNICIPIO', 'NITERÓI' em 'NITEROI', etc.
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

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    if not file_id:
        st.error("ERRO: 'file_id_convenios' não configurado nos Secrets.")
        return

    # 1. DOWNLOAD DA BASE (SE NÃO EXISTIR LOCALMENTE)
    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados volumosa..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    # 2. IDENTIFICAÇÃO DO USUÁRIO E PERMISSÕES
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.warning("Efetue o login para acessar os dados.")
        return

    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    local_permitido = str(usuario.get('local_liberado', ''))
    
    # Listas normalizadas para filtragem (NITERÓI, RIO DE JANEIRO, etc.)
    permitidos_norm = [normalizar_texto(c) for c in local_permitido.split(',') if c.strip()]
    # Gera siglas correspondentes (Ex: se tem 'RIO DE JANEIRO', adiciona 'RJ')
    siglas_permitidas = [MAPEAMENTO_UF.get(p, p) for p in permitidos_norm]

    # 3. PROCESSAMENTO EM PEDAÇOS (CHUNKING) - RESOLVE O MESSAGE SIZE ERROR
    lista_pedacos = []
    
    try:
        container_msg = st.empty()
        # Lê o arquivo em blocos de 60.000 linhas para otimizar RAM
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            container_msg.info(f"Processando base de dados... Parte {i+1} analisada.")
            
            # Padroniza nomes das colunas (Município vira MUNICÍPIO)
            chunk.columns = [str(c).strip().upper() for c in chunk.columns]
            
            # Mapeamento flexível de colunas
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c or 'CIDADE' in c), None)
            col_uf = next((c for c in chunk.columns if c in ['UF', 'ESTADO', 'SIGLA_UF', 'SIGLA UF']), 'UF')

            if col_mun:
                # Normaliza colunas do CSV para comparação justa
                chunk['MUN_NORM'] = chunk[col_mun].astype(str).apply(normalizar_texto)
                chunk['UF_NORM'] = chunk[col_uf].astype(str).apply(normalizar_texto)
                
                # --- FILTRO DE SEGURANÇA IMEDIATO POR CHUNK ---
                if "BRONZE" in plano:
                    # Filtra se a cidade normalizada estiver na lista permitida
                    chunk_f = chunk[chunk['MUN_NORM'].isin(permitidos_norm)].copy()
                elif "PRATA" in plano:
                    # Filtra se o Estado (nome ou sigla) estiver na lista permitida
                    mask_estado = (chunk['UF_NORM'].isin(permitidos_norm)) | (chunk['UF_NORM'].isin(siglas_permitidas))
                    chunk_f = chunk[mask_estado].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        container_msg.empty() 

        if lista_pedacos:
            df_base = pd.concat(lista_pedacos, ignore_index=True)
        else:
            df_base = pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum dado encontrado para a região: {local_permitido}")
        return

    # --- 4. PREPARAÇÃO DE DADOS FILTRADOS ---
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    
    # Criar coluna de Ano se não existir
    if 'ANO_FILTRO' not in df_base.columns:
        col_dt = next((c for c in df_base.columns if 'DATA' in c or 'DT' in c), None)
        if col_dt:
            df_base['ANO_FILTRO'] = pd.to_datetime(df_base[col_dt], dayfirst=True, errors='coerce').dt.year
