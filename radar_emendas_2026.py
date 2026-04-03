import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

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
    if not isinstance(texto, str): return str(texto)
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def exibir_radar():
    col_titulo, col_filtro = st.columns([2, 1])
    with col_titulo:
        st.title("🏛️ Radar de Emendas 2026")
    with col_filtro:
        tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="filtro_visao_topo")

    # IDs e Nomes de Arquivo
    if tipo_visao == "Visão Geral":
        file_id = st.secrets.get("file_id_emendas")
        nome_arquivo = "2026_Emendas_Geral.csv"
    else:
        file_id = st.secrets.get("file_id_emendas_favorecido")
        nome_arquivo = "2026_Emendas_Favorecido.csv"

    # 1. Download
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error(f"ID para '{tipo_visao}' não configurado.")
            return
        with st.spinner(f"Sincronizando {tipo_visao}..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    # 2. Leitura e Otimização de Memória
    try:
        # Lendo apenas as colunas necessárias se possível, ou tratando após leitura
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # --- CORREÇÃO 1: FILTRO DE ANO 2026 ---
        coluna_ano = next((c for c in df.columns if "ANO" in c), None)
        if coluna_ano:
            df = df[df[coluna_ano].astype(str).str.contains("2026", na=False)]

    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return

    # 3. Lógica de Segurança (UF)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    sigla_usuario = str(usuario.get('LOCALIDADE') or "RJ").strip().upper()
    nome_completo_busca = remover_acentos(MAPA_ESTADOS.get(sigla_usuario, sigla_usuario))
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    # --- CORREÇÃO 2: MAPEAMENTO DE COLUNA UF AMPLIADO ---
    # Adicionado UF_BENEFICIARIO e UF_FAVORECIDO para a base de Favorecidos
    coluna_uf = next((c for c in ["UF", "ESTADO", "UF_BENEFICIARIO", "UF_FAVORECIDO", "SIGLA_UF"] if c in df.columns), None)

    if coluna_uf:
        if not acesso_nacional:
            df['UF_BUSCA'] = df[coluna_uf].apply(remover_acentos)
            df = df[df['UF_BUSCA'] == nome_completo_busca]
            df = df.drop(columns=['UF_BUSCA'])
            st.info(f"📍 Filtro Ativo: **{nome_completo_busca}**")
    else:
        st.warning("Aviso: Localização não identificada. Exibindo dados gerais.")

    # --- CORREÇÃO 3: TRATAMENTO DE MESSAGE SIZE ERROR ---
    if df.empty:
        st.warning(f"Nenhum registro de 2026 encontrado para sua região.")
    else:
        st.divider()
        qtd_total = len(df)
        st.write(f"Registros encontrados (Ano 2026): **{qtd_total}**")
        
        # Se a base for muito grande, pedimos para filtrar antes de mostrar
        if qtd_total > 15000:
            st.warning("⚠️ Base muito grande para exibição total. Use a busca abaixo para encontrar registros específicos.")
            busca = st.text_input(f"🔍 Pesquisar em {tipo_visao} (Nome, CNPJ, Partido...):")
            if busca:
                mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
                df_filtered = df[mask]
                st.dataframe(df_filtered, use_container_width=True, hide_index=True)
            else:
                st.info("Aguardando termo de pesquisa...")
        else:
            # Se for pequena, mostra normal com busca opcional
            busca = st.text_input(f"🔍 Pesquisar em {tipo_visao}:")
            if busca:
                mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
                df = df[mask]
            st.dataframe(df, use_container_width=True, hide_index=True)
