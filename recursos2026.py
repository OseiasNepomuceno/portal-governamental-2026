# Arquivo Final - Core Essence - Debug de Permissões - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def normalizar_texto(texto):
    if pd.isna(texto) or texto is None: return ""
    nfkd_form = unicodedata.normalize('NFKD', str(texto).strip().upper())
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=True)

    # --- DIAGNÓSTICO DO USUÁRIO ---
    usuario = st.session_state.get('usuario_logado')
    
    if not usuario:
        st.error("⚠️ Erro: Usuário não identificado no sistema. Por favor, saia e faça o login novamente.")
        return

    # Tentativa flexível de pegar o local liberado (evita erro de nome de coluna)
    # Ele tenta 'local_liberado', 'LOCAL_LIBERADO', 'LOCAL' ou 'Cidades'
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or usuario.get('LOCAL') or ""
    
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    permitidos_norm = [normalizar_texto(c) for c in str(locais_bruto).split(',') if c.strip()]
    
    # Se ainda estiver vazio, o código para aqui e te avisa o que tem dentro do 'usuario'
    if not permitidos_norm and plano != "OURO" and plano != "ADMIN":
        st.error("❌ Permissão de local não encontrada no seu cadastro.")
        with st.expander("Clique aqui para ver os dados do seu login (Debug)"):
            st.write(usuario)
        return

    mapeamento_uf = {'RIO DE JANEIRO': 'RJ', 'SAO PAULO': 'SP', 'MINAS GERAIS': 'MG', 'ESPIRITO SANTO': 'ES'}
    siglas_permitidas = [mapeamento_uf.get(p, p) for p in permitidos_norm]

    lista_pedacos = []
    
    try:
        status = st.empty()
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Lendo parte {i+1} da base de dados...")
            chunk.columns = [normalizar_texto(c) for c in chunk.columns]
            
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)
            col_uf = next((c for c in chunk.columns if c in ['UF', 'ESTADO', 'SIGLA_UF']), 'UF')

            if col_mun:
                chunk['MUN_BUSCA'] = chunk[col_mun].apply(normalizar_texto)
                chunk['UF_BUSCA'] = chunk[col_uf].apply(normalizar_texto)
                
                if "BRONZE" in plano:
                    chunk_f = chunk[chunk['MUN_BUSCA'].isin(permitidos_norm)].copy()
                elif "PRATA" in plano:
                    mask = (chunk['UF_BUSCA'].isin(permitidos_norm)) | (chunk['UF_BUSCA'].isin(siglas_permitidas))
                    chunk_f = chunk[mask].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum dado encontrado para: {permitidos_norm}")
        return

    # --- EXIBIÇÃO ---
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    st.markdown("### 🔍 Pesquisa")
    termo = st.text_input("Buscar Favorecido ou Objeto:")
    
    df_f = df_base.copy()
    if termo:
        termo_n = normalizar_texto(termo)
        mask = df_f.astype(str).apply(lambda x: x.str.upper().str.contains(termo_n)).any(axis=1)
        df_f = df_f[mask]

    st.metric("Total", f"R$ {df_f['VALOR_NUM'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.dataframe(df_f.drop(columns=['MUN_BUSCA', 'UF_BUSCA', 'VALOR_NUM'], errors='ignore'), use_container_width=True)
