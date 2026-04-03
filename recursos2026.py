# Arquivo Restaurado e Reforçado - Core Essence - 03/04/2026
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
    
    # 1. DOWNLOAD REFORÇADO (Para evitar FileURLRetrievalError)
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            try:
                # fuzzy=True ajuda a encontrar o arquivo mesmo com IDs problemáticos
                gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)
            except Exception as e:
                st.error(f"Erro ao baixar base de dados: {e}")
                st.info("Certifique-se de que o arquivo no Drive está como 'Qualquer pessoa com o link'.")
                return

    # 2. LOGIN E PERMISSÕES
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.warning("Efetue o login para acessar.")
        return

    # Recupera locais e remove qualquer espaço em branco indesejado
    locais_liberados = str(usuario.get('local_liberado', '')).upper().split(',')
    locais_limpos = [c.strip() for c in locais_liberados if c.strip()]
    
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em blocos para performance e memória
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Processando dados... Bloco {i+1}")
            
            # Limpa nomes das colunas
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # Localiza coluna de município de forma flexível
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)

            if col_mun:
                # Converte coluna para string e maiúsculo para comparação
                chunk[col_mun] = chunk[col_mun].astype(str).str.upper()
                
                if plano in ["BRONZE", "PRATA"]:
                    if locais_limpos:
                        # Join com '|' faz o papel de "OU" (Ex: NITERÓI ou RIO DE JANEIRO)
                        padrao_busca = '|'.join(locais_limpos)
                        chunk_f = chunk[chunk[col_mun].str.contains(padrao_busca, na=False)].copy()
                    else:
                        chunk_f = pd.DataFrame()
                else:
                    # Plano OURO/ADMIN vê tudo
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)

        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro técnico no processamento: {e}")
        return

    # 3. EXIBIÇÃO
    if df_base.empty:
        st.error(f"❌ Nenhum dado encontrado para: {locais_limpos}")
        return

    # Tratamento de valores para somatória
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply
