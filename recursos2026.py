# Arquivo Final - Core Essence - Blindagem de Acentos e Chunks - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# --- FUNÇÃO MESTRA DE NORMALIZAÇÃO ---
def normalizar_texto(texto):
    if pd.isna(texto) or texto is None:
        return ""
    # 1. Converte para String e remove espaços extras
    texto_limpo = str(texto).strip().upper()
    # 2. Decompõe caracteres acentuados (Ex: 'Ó' vira 'O' + '´')
    nfkd_form = unicodedata.normalize('NFKD', texto_limpo)
    # 3. Filtra apenas o que não for acento e junta tudo
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

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
    
    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.warning("Por favor, faça o login para continuar.")
        return

    # --- PREPARAÇÃO DAS PERMISSÕES (SEM ACENTOS) ---
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    locais_usuario = str(usuario.get('local_liberado', ''))
    
    # Criamos a lista de cidades permitidas já normalizada (sem acentos)
    # Ex: 'NITERÓI' vira 'NITEROI'
    permitidos_norm = [normalizar_texto(c) for c in locais_usuario.split(',') if c.strip()]
    
    # Adicionamos siglas automáticas para Estados (RJ, SP, etc)
    mapeamento_uf = {'RIO DE JANEIRO': 'RJ', 'SAO PAULO': 'SP', 'MINAS GERAIS': 'MG', 'ESPIRITO SANTO': 'ES'}
    siglas_permitidas = [mapeamento_uf.get(p, p) for p in permitidos_norm]

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em blocos de 60 mil linhas para não estourar a memória (400MB)
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Analisando parte {i+1} da base de dados...")
            
            # Padroniza nomes das colunas (Ex: 'Município' -> 'MUNICIPIO')
            chunk.columns = [normalizar_texto(c) for c in chunk.columns]
            
            # Identifica as colunas principais de forma flexível
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)
            col_uf = next((c for c in chunk.columns if c in ['UF', 'ESTADO', 'SIGLA_UF']), 'UF')

            if col_mun:
                # Criamos colunas temporárias no chunk SEM ACENTOS para comparar
                chunk['MUN_BUSCA'] = chunk[col_mun].apply(normalizar_texto)
                chunk['UF_BUSCA'] = chunk[col_uf].apply(normalizar_texto)
                
                if "BRONZE" in plano:
                    # Match de cidades (ignorando acento de ambos os lados)
                    mask = chunk['MUN_BUSCA'].isin(permitidos_norm)
                    chunk_f = chunk[mask].copy()
                elif "PRATA" in plano:
                    # Match de Estado (Nome ou Sigla)
                    mask = (chunk['UF_BUSCA'].isin(permitidos_norm)) | (chunk['UF_BUSCA'].isin(siglas_permitidas))
                    chunk_f = chunk[mask].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento dos dados: {e}")
        return

    if df_base.empty:
        st.error("❌ Nenhum dado encontrado para sua região.")
        st.write(f"**Cidades/Estados buscados:** `{permitidos_norm}`")
        return

    # --- PREPARAÇÃO DE VALORES E EXIBIÇÃO ---
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    st.markdown("### 🔍 Pesquisa nos Resultados")
    termo = st.text_input("Filtrar por Favorecido ou Objeto (ex: PREFEITURA):")
    
    df_f = df_base.copy()
    if termo:
        termo_n = normalizar_texto(termo)
        # Busca insensível a acentos em todas as colunas
        mask = df_f.astype(str).apply(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper().str.contains(termo_n)).any(axis=1)
        df_f = df_f[mask]

    # Dashboard Final
    total = df_f['VALOR_NUM'].sum() if 'VALOR_NUM' in df_f.columns else 0
    st.metric("Total de Recursos Encontrados", f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Remove colunas de busca interna antes de mostrar ao usuário
    cols_para_excluir = ['MUN_BUSCA', 'UF_BUSCA', 'VALOR_NUM']
    st.dataframe(df_f.drop(columns=[c for c in cols_para_excluir if c in df_f.columns]), use_container_width=True)
