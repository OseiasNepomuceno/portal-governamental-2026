# Arquivo Otimizado - Core Essence - Somente Nomes de Localidade - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: 
        return 0.0
    try:
        # Remove R$, pontos de milhar e ajusta a vírgula para ponto decimal
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: 
        return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos 2026 (Core Essence)")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not file_id:
        st.error("ID do arquivo não configurado nos Secrets.")
        return

    # 1. DOWNLOAD DA BASE
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            try:
                gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)
            except Exception as e:
                st.error(f"Erro ao baixar base de dados: {e}")
                return

    # 2. LOGIN E PERMISSÕES
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não identificado.")
        return

    # Colunas que queremos exibir (Apenas os nomes, sem IDs ou códigos)
    termos_desejados = [
        'ANO DA EMENDA', 'TIPO DA EMENDA', 'NOME DO AUTOR DA EMENDA', 
        'MUNICÍPIO', 'UF', 'VALOR EMPENHADO', 'VALOR LIQUIDADO', 'VALOR PAGO'
    ]

    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    ver_tudo = "BRASIL" in locais_limpos or plano in ["OURO", "ADMIN", "MASTER"]

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em blocos para performance
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=80000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Processando Ciclo 2026... Bloco {i+1}")
            
            # Padroniza cabeçalhos
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # FILTRO 1: Somente Ano 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c and 'EMENDA' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]

            if chunk.empty:
                continue

            # FILTRO 2: Localidade (Regra Bronze/Prata)
            if not ver_tudo:
                # Busca a coluna de município ignorando colunas de código/IBGE
                col_mun_filtro = next((c for c in chunk.columns if 'MUNICI' in c and 'COD' not in c and 'IBGE' not in c), None)
                if col_mun_filtro:
                    padrao = '|'.join(locais_limpos)
                    chunk = chunk[chunk[col_mun_filtro].astype(str).str.upper().str.contains(padrao, na=False)]

            # SELEÇÃO FINAL: Bloqueia explicitamente colunas com 'COD', 'IBGE' ou 'ID'
            cols_finais = []
            for termo in termos_desejados:
                # Encontra a coluna que contém o termo desejado, mas que NÃO seja uma coluna de código
                encontrada = next((c for c in chunk.columns if termo in c and 'COD' not in c and 'IBGE' not in c and 'ID' not in c), None)
                if encontrada:
                    cols_finais.append(encontrada)
            
            # Remove duplicatas da lista de colunas
            cols_finais = list(dict.fromkeys(cols_finais))
            
            if cols_finais:
                chunk_f = chunk[cols_finais].copy()
                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)

        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum recurso de 2026 localizado para: {locais
