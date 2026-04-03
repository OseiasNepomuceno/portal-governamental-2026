# Arquivo Restaurado e Blindado - Core Essence - 03/04/2026
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
    
    nome_arquivo = "20260320_Convenios.csv"
    file_id = st.secrets.get("file_id_convenios")
    
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=True)

    # --- RECAPTURANDO O USUÁRIO (COM REDE DE SEGURANÇA) ---
    usuario = st.session_state.get('usuario_logado')
    
    if not usuario:
        st.error("⚠️ Sessão expirada ou usuário não logado.")
        return

    # Tenta pegar as cidades de qualquer jeito (vários nomes possíveis)
    locais_bruto = (
        usuario.get('local_liberado') or 
        usuario.get('LOCAL_LIBERADO') or 
        usuario.get('cidades') or 
        usuario.get('municipios') or ""
    )
    
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    # Prepara a lista de busca (Como você colocou acentos na planilha, vamos usar exatamente o que vier)
    locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]

    # --- SE A LISTA CONTINUAR VAZIA, PARAMOS AQUI PARA VOCÊ VER O PORQUÊ ---
    if not locais_limpos and plano not in ["OURO", "ADMIN"]:
        st.error("❌ Erro de Configuração: Não encontramos cidades liberadas no seu perfil.")
        with st.expander("Clique aqui para ver os dados do seu Login (Debug)"):
            st.write("Estes são os dados que o sistema recebeu do seu login:")
            st.json(usuario)
            st.info("Verifique se o nome da coluna na sua planilha de usuários é exatamente 'local_liberado'")
        return

    lista_pedacos = []
    
    try:
        status = st.empty()
        # Lendo em pedaços (Chunks) para não dar erro de memória (400MB)
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', 
                             on_bad_lines='skip', chunksize=60000)
        
        for i, chunk in enumerate(reader):
            status.info(f"Processando bloco {i+1}...")
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            col_mun = next((c for c in chunk.columns if 'MUNICI' in c), None)

            if col_mun:
                # Busca por aproximação (Igual ontem à noite)
                if plano in ["BRONZE", "PRATA"]:
                    padrao = '|'.join(locais_limpos)
                    # Filtra se o nome da cidade no CSV CONTÉM algum dos seus locais
                    chunk_f = chunk[chunk[col_mun].astype(str).str.upper().str.contains(padrao, na=False)].copy()
                else:
                    chunk_f = chunk.copy()

                if not chunk_f.empty:
                    lista_pedacos.append(chunk_f)
        
        status.empty()
        df_base = pd.concat(lista_pedacos, ignore_index=True) if lista_pedacos else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro técnico ao ler o CSV: {e}")
        return

    # --- EXIBIÇÃO FINAL ---
    if df_base.empty:
        st.warning(f"Nenhum dado encontrado no CSV para: {locais_limpos}")
        return

    col_valor = next((c for c in df_base.columns if 'VALOR' in c), None)
    if col_valor:
        df_base['VALOR_NUM'] = df_base[col_valor].apply(limpar_valor_monetario)

    st.metric("Total dos Recursos", f"R$ {df_base['VALOR_NUM'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.dataframe(df_base.drop(columns=['VALOR_NUM'], errors='ignore'), use_container_width=True)
