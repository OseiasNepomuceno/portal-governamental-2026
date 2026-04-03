# Arquivo Otimizado - Core Essence - Foco 2026 e Colunas Essenciais - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos 2026 (Core Essence)")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not file_id:
        st.error("ID do arquivo não configurado nos Secrets.")
        return

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não identificado.")
        return

    # --- DEFINIÇÃO DE COLUNAS DE INTERESSE ---
    colunas_desejadas = [
        'ANO DA EMENDA', 'TIPO DA EMENDA', 'NOME DO AUTOR DA EMENDA', 
        'MUNICÍPIO', 'UF', 'VALOR EMPENHADO', 'VALOR LIQUIDADO', 'VALOR PAGO'
    ]

    # --- LÓGICA DE PERMISSÃO ---
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    ver_tudo = "BRASIL" in locais_limpos or plano in ["OURO", "ADMIN", "MASTER"]

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em blocos maiores (80k) já que estamos filtrando colunas, sobra mais RAM
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=80000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Processando Ciclo 2026... Bloco {i+1}")
            
            # 1. Padroniza colunas para identificar os nomes reais no CSV
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # 2. FILTRO IMEDIATO: Somente Ano 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c and 'EMENDA' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]

            if chunk.empty:
                continue

            # 3. FILTRO DE LOCALIDADE (Aplica a mesma norma para todos)
            if not ver_tudo:
                col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)
                if col_mun:
                    padrao = '|'.join(locais_limpos)
                    chunk = chunk[chunk[col_mun].astype(str).str.upper().str.contains(padrao, na=False)]

            # 4. SELEÇÃO DE COLUNAS (Mantém apenas as 8 colunas de interesse)
            # Buscamos as colunas que possuem os nomes solicitados
            cols_finais = []
            for ref in colunas_desejadas:
                encontrada = next((c for c in chunk.columns if ref.upper() in c), None)
                if encontrada: cols_finais.append(encontrada)
            
            chunk = chunk[cols_finais].copy()

            if not chunk.empty:
                lista_pedacos.append(chunk)

        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento otimizado: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum recurso de 2026 localizado para: {locais_limpos}")
        return

    # --- CÁLCULOS PARA O DASHBOARD ---
    # Identifica a coluna de Valor Pago para a métrica
    col_pago = next((c for c in df_base.columns if 'PAGO' in c), None)
    if col_pago:
        df_base['VALOR_PAGO_SOMA'] = df_base[col_pago].apply(limpar_valor_monetario)
        total_pago = df_base['VALOR_PAGO_SOMA'].sum()
        st.metric("Total Pago (Exercício 2026)", f"R$ {total_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Exibe a tabela apenas com as colunas solicitadas
    st.dataframe(df_base.drop(columns=['VALOR_PAGO_SOMA'], errors='ignore'), use_container_width=True)
