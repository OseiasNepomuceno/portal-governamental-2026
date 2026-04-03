# Arquivo Restaurado - Core Essence - Versão Estável - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: return 0.0
    try:
        # Limpeza padrão que funcionava ontem
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    # 1. DOWNLOAD (IGUAL AO QUE FUNCIONAVA)
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    # 2. LOGIN E PERMISSÕES
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.warning("Efetue o login para acessar.")
        return

    # Pegamos os locais exatamente como você digitou na planilha (com ou sem acento)
    locais_liberados = str(usuario.get('local_liberado', '')).upper().split(',')
    locais_limpos = [c.strip() for c in locais_liberados if c.strip()]
    
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()

    lista_pedacos = []
    
    try:
        # Lendo em pedaços para não travar (Única mudança "nova" mantida para segurança)
        # sep=None faz o pandas descobrir se é vírgula ou ponto-e-vírgula sozinho
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=70000)
        
        for chunk in reader:
            # Padroniza colunas para maiúsculo
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # Localiza colunas (Ontem funcionava buscando Município ou UF)
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)
            col_uf = next((c for c in chunk.columns if 'UF' in c or 'ESTADO' in c), 'UF')

            if col_mun:
                # CONDIÇÃO DE FILTRO VOLTANDO AO QUE ERA ONTEM:
                # Se o plano for BRONZE, filtra pelas cidades na lista locais_limpos
                if "BRONZE" in plano:
                    # O .str.contains com join '|' é o jeito mais certeiro de achar 'NITERÓI' dentro de 'PREFEITURA DE NITERÓI'
                    padrao = '|'.join(locais_limpos)
                    chunk_f = chunk[chunk[col_mun].astype(str).str.upper().str.contains(padrao, na=False)].copy()
                
                elif "PRATA" in plano:
                    # Filtra pelo Estado (Ex: RJ ou Rio de Janeiro)
                    padrao = locales_limpos[0] if locais_limpos else ""
                    chunk_f = chunk[chunk[col_uf].astype(str).str.upper().str.contains(padrao, na=False)].copy()
                
                else: # OURO / ADMIN
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)

        # Junta os resultados filtrados
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return

    # 3. EXIBIÇÃO DOS RESULTADOS
    if df_base.empty:
        st.error(f"❌ Nenhum dado encontrado para: {locais_limpos}")
        st.info("Dica: Verifique se os nomes na sua planilha de usuários batem com o CSV.")
        return

    # Converte valores para número
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUMERICO'] = df_base[col_valor].apply(limpar_valor_monetario)

    # Filtro de busca na tela
    st.markdown("---")
    busca = st.text_input("Filtrar na tabela (Ex: Prefeitura, Fundo, etc):")
    
    df_exibir = df_base.copy()
    if busca:
        df_exibir = df_exibir[df_exibir.astype(str).apply(lambda x: x.str.upper().contains(busca.upper())).any(axis=1)]

    # Métricas e Tabela
    total = df_exibir['VALOR_NUMERICO'].sum() if 'VALOR_NUMERICO' in df_exibir.columns else 0
    st.metric("Soma dos Recursos", f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Mostra a tabela limpando colunas extras de sistema
    st.dataframe(df_exibir.drop(columns=['VALOR_NUMERICO'], errors='ignore'), use_container_width=True)
