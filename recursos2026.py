import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: 
        return 0.0
    try:
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: 
        return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos 2026")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not file_id:
        st.error("Configure 'file_id_convenios' nos Secrets.")
        return

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- IDENTIFICAÇÃO NO MENU LATERAL ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Perfil de Acesso")
        
        nome_display = usuario.get('NOME') or usuario.get('USUARIO') or "Usuário"
        st.info(f"**Login:** {nome_display}")
        
        plano_display = str(usuario.get('PLANO', 'BRONZE')).upper()
        st.success(f"**Plano:** {plano_display}")

        tipo_consultor = usuario.get('TIPO_CONSULTOR') or usuario.get('TIPO') or "Consultor"
        st.warning(f"**Tipo:** {tipo_consultor}")

        # Pega a UF liberada (Ex: RJ, SP, MG)
        uf_liberada = str(usuario.get('UF_LIBERADA') or usuario.get('UF') or "").strip().upper()
        st.write(f"🌎 **Estado Liberado:** {uf_liberada}")
        st.divider()

    # --- CONFIGURAÇÃO DE FILTROS ---
    # Se o plano for alto ou a UF for "BRASIL", ele vê tudo
    ver_tudo = uf_liberada in ["BRASIL", "TODOS", ""] or plano_display in ["OURO", "ADMIN", "MASTER"]

    # Colunas para a tabela final
    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']

    lista_final = []
    
    try:
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=85000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # 1. FILTRO ANO 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. FILTRO POR UF (ESTADO)
            if not ver_tudo:
                # Localiza a coluna UF exata (evitando colunas de código)
                col_uf_csv = next((c for c in chunk.columns if c == 'UF' or ( 'UF' in c and 'COD' not in c)), None)
                if col_uf_csv:
                    # Filtra apenas o estado do consultor (Ex: RJ)
                    chunk = chunk[chunk[col_uf_csv].astype(str).upper() == uf_liberada]

            if chunk.empty: continue

            # SELEÇÃO DE COLUNAS
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c), None)
                if encontrada: cols_ok.append(encontrada)
            
            cols_ok = list(dict.fromkeys(cols_ok))
            if cols_ok:
                lista_final.append(chunk[cols_ok].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    # --- EXIBIÇÃO ---
    if df_base.empty:
        st.warning(f"Nenhum dado de 2026 encontrado para o estado: {uf_liberada}")
        return

    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)
    if col_e:
        v_e = df_base[col_e].apply(limpar_valor).sum()
        m1.metric("Total Empenhado (Estado)", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    if col_p:
        v_p = df_base[col_p].apply(limpar_valor).sum()
        m2.metric("Total Pago (Estado)", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    st.dataframe(df_base, use_container_width=True)
