# Arquivo Atualizado - Core Essence - Processamento por Partes (Chunks) - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# --- FUNÇÃO DE NORMALIZAÇÃO (IGNORA ACENTOS E MAIÚSCULAS) ---
def normalizar_texto(texto):
    if pd.isna(texto) or texto is None:
        return ""
    # Transforma 'MUNICÍPIO' em 'MUNICIPIO' e 'Rio de Janeiro' em 'RIO DE JANEIRO'
    nfkd_form = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).strip().upper()

# --- FUNÇÃO DE LIMPEZA MONETÁRIA ---
def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]:
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except:
        return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    if not file_id:
        st.error("ERRO: 'file_id_convenios' não configurado nos Secrets.")
        return

    # 1. DOWNLOAD DA BASE (SE NÃO EXISTIR LOCALMENTE)
    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados volumosa..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    # 2. IDENTIFICAÇÃO DO USUÁRIO E PERMISSÕES
    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.warning("Efetue o login para acessar os dados.")
        return

    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    local_permitido = str(usuario.get('local_liberado', ''))
    # Lista normalizada das cidades/estados da Gláucia
    permitidos_norm = [normalizar_texto(c) for c in local_permitido.split(',') if c.strip()]

    # 3. PROCESSAMENTO EM PEDAÇOS (CHUNKING) - RESOLVE O MESSAGE SIZE ERROR
    lista_pedacos = []
    
    try:
        container_msg = st.empty()
        # Lê o arquivo em blocos de 50.000 linhas
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=50000)
        
        for i, chunk in enumerate(reader):
            container_msg.info(f"Filtrando dados... Parte {i+1} processada.")
            
            # Padroniza nomes das colunas
            chunk.columns = [str(c).strip().upper() for c in chunk.columns]
            
            # Mapeia colunas (Município com ou sem acento vira MUNICÍPIO após .upper())
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c or 'CIDADE' in c), None)
            col_uf = next((c for c in chunk.columns if c in ['UF', 'ESTADO', 'SIGLA_UF']), 'UF')

            if col_mun:
                # Normaliza a coluna do CSV no pedaço atual
                chunk['MUN_NORM'] = chunk[col_mun].apply(normalizar_texto)
                
                # FILTRO DE SEGURANÇA IMEDIATO
                if "BRONZE" in plano:
                    chunk_f = chunk[chunk['MUN_NORM'].isin(permitidos_norm)].copy()
                elif "PRATA" in plano:
                    estado_alvo = permitidos_norm[0] if permitidos_norm else ""
                    chunk['UF_NORM'] = chunk[col_uf].apply(normalizar_texto)
                    chunk_f = chunk[chunk['UF_NORM'] == estado_alvo].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        container_msg.empty() # Remove aviso de processamento

        if lista_pedacos:
            df_base = pd.concat(lista_pedacos, ignore_index=True)
        else:
            df_base = pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return

    if df_base.empty:
        st.warning("Nenhum dado encontrado para sua região de acesso.")
        return

    # --- 4. PREPARAÇÃO DE DADOS FILTRADOS ---
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    
    # Criar coluna de Ano se não existir
    if 'ANO_FILTRO' not in df_base.columns:
        col_dt = next((c for c in df_base.columns if 'DATA' in c or 'DT' in c), None)
        if col_dt:
            df_base['ANO_FILTRO'] = pd.to_datetime(df_base[col_dt], dayfirst=True, errors='coerce').dt.year
            df_base['ANO_FILTRO'] = df_base['ANO_FILTRO'].fillna(0).astype(int).astype(str)
        else:
            df_base['ANO_FILTRO'] = "2026"

    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    # --- 5. INTERFACE DE BUSCA E FILTROS ---
    st.markdown("### 🔍 Busca e Filtros")
    termo = st.text_input("Digite o que procura (Município, Favorecido ou Objeto):")
    
    c1, c2 = st.columns(2)
    with c1:
        opcoes_ano = ["Todos"] + sorted(df_base['ANO_FILTRO'].unique().tolist(), reverse=True)
        filtro_ano = st.selectbox("Ano:", opcoes_ano)
    with c2:
        # Aqui o Estado estará travado apenas no que o plano permite (Ex: RIO DE JANEIRO)
        opcoes_uf = ["Todos"] + sorted(df_base[col_uf].dropna().unique().tolist())
        filtro_uf = st.selectbox("Estado (UF):", opcoes_uf)

    # Filtros de Tela Ativos
    df_f = df_base.copy()
    if filtro_ano != "Todos":
        df_f = df_f[df_f['ANO_FILTRO'] == filtro_ano]
    if filtro_uf != "Todos":
        df_f = df_f[df_f[col_uf] == filtro_uf]
    if termo:
        termo_n = normalizar_texto(termo)
        # Busca inteligente em todas as colunas
        mask = df_f.astype(str).apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper().str.contains(termo_n)).any(axis=1)
        df_f = df_f[mask]

    # --- 6. EXIBIÇÃO FINAL ---
    st.markdown("---")
    if not df_f.empty:
        total = df_f['VALOR_NUM'].sum()
        total_fmt = f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.metric("Soma Total dos Recursos", total_fmt)
        
        # Oculta colunas auxiliares
        cols_final = [c for c in df_f.columns if '_NORM' not in c and 'VALOR_NUM' != c]
        st.dataframe(df_f[cols_final], use_container_width=True)
    else:
        st.metric("Total Encontrado", "R$ 0,00")
        st.info("Nenhum registro corresponde aos filtros selecionados.")
