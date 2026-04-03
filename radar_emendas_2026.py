import streamlit as st
import pandas as pd
import gdown
import os

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares 2026")

    # 1. Configurações de Identificação do Arquivo
    file_id = st.secrets.get("file_id_emendas")
    nome_arquivo = "2026_Emendas.csv"

    # 2. VERIFICAÇÃO E DOWNLOAD (Resolve o erro: No such file or directory)
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("ERRO: 'file_id_emendas' não configurado no st.secrets.")
            return
            
        with st.spinner("Sincronizando Base de Emendas..."):
            try:
                url = f'https://drive.google.com/uc?id={file_id}'
                gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)
            except Exception as e:
                st.error(f"Erro ao baixar base de dados: {e}")
                return

    # 3. LEITURA DA BASE (Resolve o erro: low_memory / engine python)
    try:
        df = pd.read_csv(
            nome_arquivo, 
            sep=None, 
            engine='python', 
            encoding='latin1', 
            on_bad_lines='skip'
        )
        
        # Padroniza nomes de colunas (remove espaços e coloca em MAIÚSCULO)
        df.columns = [str(c).upper().strip() for c in df.columns]

    except Exception as e:
        st.error(f"Não foi possível carregar a base: Erro na leitura: {e}")
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        return

    # 4. LÓGICA DE FILTROS POR PLANO E ESTADO (CORRIGIDA PARA EVITAR ATTRIBUTEERROR)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    # Recupera a localidade do cadastro
    local_cadastrado = str(usuario.get('LOCALIDADE') or usuario.get('LOCAL_LIBERADO') or "RJ").strip().upper()
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    # --- BUSCA AUTOMÁTICA PELA COLUNA DE UF ---
    coluna_uf = None
    possiveis_nomes = ["UF", "ESTADO", "SIGLA", "U.F.", "SG_UF"]
    
    for c in possiveis_nomes:
        if c in df.columns:
            coluna_uf = c
            break

    if not acesso_nacional:
        if coluna_uf:
            # Aplica o filtro na coluna encontrada
            df = df[df[coluna_uf].astype(str).str.strip().upper() == local_cadastrado]
            st.info(f"📍 Filtro Ativo: **{local_cadastrado}** (Coluna identificada: {coluna_uf})")
        else:
            # Caso não encontre nenhuma coluna de UF, avisa o usuário em vez de travar o app
            st.warning("⚠️ Atenção: Não foi possível filtrar por Estado pois a coluna 'UF' ou 'ESTADO' não foi detectada na planilha.")
            st.write("Colunas disponíveis na base:", list(df.columns))

    elif acesso_nacional:
        st.success(f"✅ Acesso Nacional Liberado (Plano {plano})")

    # 5. EXIBIÇÃO DOS RESULTADOS
    if df.empty:
        st.warning(f"Nenhum registro encontrado para a localidade: {local_cadastrado}")
    else:
        st.write(f"Exibindo **{len(df)}** registros encontrados.")
        
        # Converte colunas de valor para numérico para evitar erros de exibição
        colunas_valor = [c for c in df.columns if "VALOR" in c or "VAL" in c]
        for col in colunas_valor:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True
        )
