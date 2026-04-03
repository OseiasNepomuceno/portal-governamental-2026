# Arquivo Finalizado - Core Essence - Match Flexível - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def normalizar(texto):
    if pd.isna(texto) or texto is None: return ""
    nfkd = unicodedata.normalize('NFKD', str(texto).strip().upper())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

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
        with st.spinner("Sincronizando base de dados..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não identificado.")
        return

    # 1. PREPARAÇÃO DOS TERMOS (SEM ACENTO PARA BUSCA INTERNA)
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    # Transformamos NITERÓI em NITEROI para a busca no motor
    termos_busca = [normalizar(c) for c in str(locais_bruto).split(',') if c.strip()]
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em pedaços para não travar a memória
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=65000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Vasculhando base de dados... Parte {i+1}")
            
            # Padroniza colunas
            chunk.columns = [normalizar(c) for c in chunk.columns]
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)

            if col_mun:
                # Criamos uma versão da coluna MUNICIPIO sem acentos apenas para o filtro
                # Isso garante que NITEROI (seu login) ache NITERÓI (no CSV)
                chunk['MUN_LIMPO'] = chunk[col_mun].astype(str).apply(normalizar)
                
                if "BRONZE" in plano or "PRATA" in plano:
                    # O pulo do gato: Regex que ignora o que vem antes ou depois
                    # Ex: Se buscar 'NITEROI', ele acha 'PREFEITURA DE NITERÓI'
                    padrao_regex = '|'.join(termos_busca)
                    chunk_f = chunk[chunk['MUN_LIMPO'].str.contains(padrao_regex, na=False, case=False)].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao ler os dados: {e}")
        return

    # 2. EXIBIÇÃO DOS RESULTADOS
    if df_base.empty:
        st.warning(f"Nenhum dado encontrado para: {termos_busca}")
        st.info("Dica: Certifique-se de que o arquivo CSV no Drive contém dados dessas cidades.")
        return

    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    # Dashboard
    st.metric("Total dos Recursos Localizados", f"R$ {df_base['VALOR_NUM'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Busca manual na tela
    busca_tela = st.text_input("Refinar busca nos resultados (Ex: Saúde, Educação):")
    if busca_tela:
        termo_tela = normalizar(busca_tela)
        mask = df_base.astype(str).apply(lambda x: x.str.upper().str.contains(termo_tela)).any(axis=1)
        df_base = df_base[mask]

    # Mostra a tabela limpa
    st.dataframe(df_base.drop(columns=['MUN_LIMPO', 'VALOR_NUM'], errors='ignore'), use_container_width=True)
