# Arquivo Finalizado - Core Essence - Ajuste Brasil - 03/04/2026
import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor_monetario(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos (Core Essence)")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not file_id:
        st.error("ID do arquivo não configurado nos Secrets.")
        return

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não identificado.")
        return

    # --- LÓGICA DE PERMISSÃO ---
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()

    # REGRA ESPECIAL: Se estiver escrito BRASIL ou for Plano Ouro/Admin, não filtra por cidade
    ver_tudo = "BRASIL" in locais_limpos or plano in ["OURO", "ADMIN", "MASTER"]

    lista_pedacos = []
    
    try:
        status = st.empty()
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=70000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Analisando dados... Parte {i+1}")
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            if ver_tudo:
                # Se for para ver tudo, adiciona o bloco inteiro
                lista_pedacos.append(chunk)
            else:
                # Caso contrário, filtra pelas cidades (Niterói, etc)
                col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)
                if col_mun:
                    padrao = '|'.join(locais_limpos)
                    mask = chunk[col_mun].astype(str).str.upper().str.contains(padrao, na=False)
                    chunk_f = chunk[mask].copy()
                    if not chunk_f.empty:
                        lista_pedacos.append(chunk_f)

        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    if df_base.empty:
        st.warning(f"Nenhum dado encontrado para: {locais_limpos}")
        return

    # --- EXIBIÇÃO ---
    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    total = df_base['VALOR_NUM'].sum() if 'VALOR_NUM' in df_base.columns else 0
    st.metric("Total de Recursos", f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.dataframe(df_base.drop(columns=['VALOR_NUM'], errors='ignore'), use_container_width=True)
