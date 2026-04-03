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

    # IDs do Drive
    if tipo_visao == "Visão Geral":
        file_id = st.secrets.get("file_id_emendas")
        nome_arquivo = "2026_Emendas_Geral.csv"
    else:
        file_id = st.secrets.get("file_id_emendas_favorecido")
        nome_arquivo = "2026_Emendas_Favorecido.csv"

    # 1. Download (Sincronização)
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error(f"ID de arquivo não configurado para {tipo_visao}.")
            return
        with st.spinner(f"Baixando base de {tipo_visao}..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    # 2. Leitura e Limpeza Inicial
    try:
        # Lendo a base (sep=None identifica se é , ou ;)
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # --- FILTRO DE ANO 2026 (OBRIGATÓRIO) ---
        coluna_ano = next((c for c in df.columns if "ANO" in c), None)
        if coluna_ano:
            df = df[df[coluna_ano].astype(str).str.contains("2026", na=False)]
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return

    # 3. Lógica de Segurança por Estado (UF)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    sigla_usuario = str(usuario.get('LOCALIDADE') or "RJ").strip().upper()
    nome_completo_busca = remover_acentos(MAPA_ESTADOS.get(sigla_usuario, sigla_usuario))
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    # Mapeamento estendido de nomes de colunas de UF
    coluna_uf = next((c for c in ["UF", "ESTADO", "UF_BENEFICIARIO", "UF_FAVORECIDO", "SG_UF", "SIGLA_UF"] if c in df.columns), None)

    if coluna_uf and not acesso_nacional:
        df['UF_AUX'] = df[coluna_uf].apply(remover_acentos)
        df = df[df['UF_AUX'] == nome_completo_busca]
        df = df.drop(columns=['UF_AUX'])
        st.info(f"📍 Exibindo: **{nome_completo_busca}**")
    elif not coluna_uf and not acesso_nacional:
        st.warning("⚠️ Localização não identificada na planilha. Exibindo todos os estados.")

    # 4. Exibição Inteligente (Evita erro de 200MB)
    if df.empty:
        st.warning("Nenhum dado de 2026 encontrado para os critérios selecionados.")
    else:
        total_linhas = len(df)
        st.write(f"Registros de 2026 encontrados: **{total_linhas}**")
        
        # Se passar de 10 mil linhas, o Streamlit exige uma busca textual para não travar
        if total_linhas > 10000:
            st.warning("🔍 A base é muito grande. **Digite um nome, CNPJ ou Cidade** abaixo para visualizar:")
            termo = st.text_input("Filtrar resultados:", key="busca_grande", placeholder="Ex: Rio de Janeiro, Prefeitura, Nome do Deputado...")
            if termo:
                # Busca em todas as colunas
                mask = df.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
                st.dataframe(df[mask], use_container_width=True, hide_index=True)
            else:
                st.info("Aguardando termo de pesquisa para exibir os dados...")
        else:
            # Se for menor, mostra direto e permite busca opcional
            termo = st.text_input("Filtrar resultados (opcional):", key="busca_pequena")
            if termo:
                mask = df.astype(str).apply(lambda x: x.str.contains(termo, case=False)).any(axis=1)
                df = df[mask]
            st.dataframe(df, use_container_width=True, hide_index=True)
