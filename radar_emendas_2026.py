import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def remover_acentos(texto):
    """Função para transformar 'SÃO' em 'SAO', 'CEARÁ' em 'CEARA', etc."""
    if not isinstance(texto, str):
        return texto
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares 2026")

    # 1. Configurações de Identificação do Arquivo
    file_id = st.secrets.get("file_id_emendas")
    nome_arquivo = "2026_Emendas.csv"

    # 2. VERIFICAÇÃO E DOWNLOAD
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

    # 3. LEITURA DA BASE
    try:
        df = pd.read_csv(
            nome_arquivo, 
            sep=None, 
            engine='python', 
            encoding='latin1', 
            on_bad_lines='skip'
        )
        
        # Padroniza nomes de colunas (MAIÚSCULO E SEM ESPAÇOS)
        df.columns = [str(c).strip().upper() for c in df.columns]

    except Exception as e:
        st.error(f"Não foi possível carregar a base: {e}")
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        return

    # 4. LÓGICA DE FILTROS COM NORMALIZAÇÃO (CORREÇÃO DE ACENTOS)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    # Normaliza o local buscado (Ex: 'São Paulo' vira 'SAO PAULO')
    local_busca = remover_acentos(usuario.get('LOCALIDADE') or "RJ")
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    if "UF" in df.columns:
        if not acesso_nacional:
            # CRIAMOS UMA COLUNA TEMPORÁRIA SEM ACENTOS PARA FILTRAR
            # Isso garante que 'PARÁ' e 'PARA' sejam encontrados da mesma forma
            df['UF_NORMALIZADA'] = df['UF'].apply(remover_acentos)
            
            # Aplica o filtro na coluna sem acentos
            df = df[df['UF_NORMALIZADA'] == local_busca]
            
            # Remove a coluna temporária para não poluir a visualização
            df = df.drop(columns=['UF_NORMALIZADA'])
            
            st.info(f"📍 Filtro Inteligente Ativo: **{local_busca}** (Ignorando acentos)")
        else:
            st.success(f"✅ Acesso Nacional Liberado (Plano {plano})")
    else:
        st.error("⚠️ Coluna 'UF' não encontrada na planilha!")
        st.write("Colunas detectadas:", list(df.columns))
        return

    # 5. EXIBIÇÃO DOS RESULTADOS
    if df.empty:
        st.warning(f"Nenhum registro encontrado para: {local_busca}")
    else:
        st.write(f"Exibindo **{len(df)}** registros encontrados.")
        
        # Converte valores financeiros para exibição limpa
        for col in df.columns:
            if "VALOR" in col or "VAL" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        st.dataframe(df, use_container_width=True, hide_index=True)
