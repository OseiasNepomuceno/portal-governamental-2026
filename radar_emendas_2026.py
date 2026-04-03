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
    # --- CABEÇALHO COM FILTRO NO TOPO DIREITO ---
    col_titulo, col_filtro = st.columns([2, 1])
    
    with col_titulo:
        st.title("🏛️ Radar de Emendas 2026")
        
    with col_filtro:
        tipo_visao = st.selectbox(
            "Selecione a Visualização:",
            ["Visão Geral", "Por Favorecido"],
            index=0,
            key="filtro_visao_topo"
        )

    # Definição do ID do arquivo baseado na escolha
    if tipo_visao == "Visão Geral":
        file_id = st.secrets.get("file_id_emendas")
        nome_arquivo = "2026_Emendas_Geral.csv"
    else:
        file_id = st.secrets.get("file_id_emendas_favorecido") 
        nome_arquivo = "2026_Emendas_Favorecido.csv"

    # 1. Download do arquivo escolhido
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error(f"Erro: ID para '{tipo_visao}' não configurado no Secrets.")
            return
        with st.spinner(f"Sincronizando {tipo_visao}..."):
            try:
                url = f'https://drive.google.com/uc?id={file_id}'
                gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)
            except Exception as e:
                st.error(f"Erro no download: {e}")
                return

    # 2. Leitura da Base
    try:
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return

    # 3. Lógica de Segurança (Plano e Estado)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    sigla_usuario = str(usuario.get('LOCALIDADE') or "RJ").strip().upper()
    
    # Converte para nome completo para bater com a planilha
    nome_completo_busca = remover_acentos(MAPA_ESTADOS.get(sigla_usuario, sigla_usuario))
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    # Identifica a coluna de UF (pode variar entre os dois arquivos)
    coluna_uf = "UF" if "UF" in df.columns else "ESTADO" if "ESTADO" in df.columns else None

    if coluna_uf:
        if not acesso_nacional:
            # Aplica normalização para garantir que nomes como 'RIO DE JANEIRO' funcionem
            df['UF_BUSCA'] = df[coluna_uf].apply(remover_acentos)
            df = df[df['UF_BUSCA'] == nome_completo_busca]
            df = df.drop(columns=['UF_BUSCA'])
            st.info(f"📍 Exibindo dados de: **{nome_completo_busca}**")
        else:
            st.success(f"✅ Acesso Nacional Liberado - {tipo_visao}")
    else:
        st.warning("Aviso: Coluna de localização não identificada para filtro automático.")

    # 4. Exibição e Busca Interna
    if df.empty:
        st.warning(f"Nenhum registro encontrado em '{tipo_visao}' para sua região.")
    else:
        st.divider()
        st.write(f"Total de registros: **{len(df)}**")
        
        # Filtro de busca textual rápido para o consultor
        busca = st.text_input(f"🔍 Pesquisar em {tipo_visao} (Nome, CNPJ, Partido...):", placeholder="Digite para filtrar a tabela abaixo...")
        if busca:
            mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True)
