import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# Dicionário para converter Sigla em Nome Completo
MAPA_ESTADOS = {
    'AC': 'ACRE', 'AL': 'ALAGOAS', 'AP': 'AMAPA', 'AM': 'AMAZONAS', 'BA': 'BAHIA',
    'CE': 'CEARA', 'DF': 'DISTRITO FEDERAL', 'ES': 'ESPIRITO SANTO', 'GO': 'GOIAS',
    'MA': 'MARANHAO', 'MT': 'MATO GROSSO', 'MS': 'MATO GROSSO DO SUL', 'MG': 'MINAS GERAIS',
    'PA': 'PARA', 'PB': 'PARAIBA', 'PR': 'PARANA', 'PE': 'PERNAMBUCO', 'PI': 'PIAUI',
    'RJ': 'RIO DE JANEIRO', 'RN': 'RIO GRANDE DO NORTE', 'RS': 'RIO GRANDE DO SUL',
    'RO': 'RONDONIA', 'RR': 'RORAIMA', 'SC': 'SANTA CATARINA', 'SP': 'SAO PAULO',
    'SE': 'SERGIPE', 'TO': 'TOCANTINS'
}

def remover_acentos(texto):
    if not isinstance(texto, str):
        return str(texto)
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def exibir_radar():
    st.title("🏛️ Radar de Emendas Parlamentares 2026")

    file_id = st.secrets.get("file_id_emendas")
    nome_arquivo = "2026_Emendas.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando Base de Emendas..."):
            try:
                url = f'https://drive.google.com/uc?id={file_id}'
                gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)
            except Exception as e:
                st.error(f"Erro ao baixar base: {e}")
                return

    try:
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return

    # --- LÓGICA DE FILTRO POR NOME COMPLETO ---
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    # Pega a sigla (ex: RJ) e converte para nome completo (ex: RIO DE JANEIRO)
    sigla_usuario = str(usuario.get('LOCALIDADE') or "RJ").strip().upper()
    nome_completo_busca = MAPA_ESTADOS.get(sigla_usuario, sigla_usuario) 
    
    # Normaliza para garantir (remove acentos se houver no dicionário ou cadastro)
    nome_completo_busca = remover_acentos(nome_completo_busca)
    
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    if "UF" in df.columns:
        if not acesso_nacional:
            # Normaliza a coluna UF da planilha (transforma 'SÃO PAULO' em 'SAO PAULO')
            df['UF_BUSCA'] = df['UF'].apply(remover_acentos)
            
            # Filtra pelo nome completo normalizado
            df = df[df['UF_BUSCA'] == nome_completo_busca]
            df = df.drop(columns=['UF_BUSCA'])
            
            st.info(f"📍 Filtro Ativo: **{nome_completo_busca}**")
        else:
            st.success(f"✅ Acesso Nacional Liberado")
    else:
        st.error("Coluna 'UF' não encontrada.")
        return

    if df.empty:
        st.warning(f"Nenhum registro encontrado para: {nome_completo_busca}")
    else:
        st.write(f"Encontrados: **{len(df)}** registros.")
        st.dataframe(df, use_container_width=True, hide_index=True)
