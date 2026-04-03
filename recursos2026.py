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
        st.error("ID do arquivo não configurado.")
        return

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- LÓGICA DE PERMISSÃO ---
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
    
    # IMPORTANTE: Pegamos a UF diretamente do cadastro do usuário para travar a planilha
    uf_usuario = str(usuario.get('UF') or usuario.get('UF_LIBERADA') or "").strip().upper()

    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Perfil de Acesso")
        st.info(f"**Login:** {usuario.get('NOME') or 'Usuário'}")
        st.success(f"**Plano:** {plano}")
        if not uf_usuario == "BRASIL":
            st.warning(f"📍 **Estado Restrito:** {uf_usuario}")
        st.divider()

    # Se for Plano Ouro/Master ou UF for BRASIL, libera tudo
    ver_tudo = uf_usuario in ["BRASIL", "TODOS"] or plano in ["OURO", "ADMIN", "MASTER"]

    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']
    lista_final = []
    
    try:
        # Lendo o arquivo em blocos
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=90000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # 1. FILTRO OBRIGATÓRIO: ANO 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. FILTRO DE SEGURANÇA MÁXIMA: TRAVA POR UF
            if not ver_tudo and uf_usuario:
                col_uf_csv = next((c for c in chunk.columns if c == 'UF' or (len(c) == 2 and 'UF' in c)), None)
                if col_uf_csv:
                    # Mantém APENAS as linhas que batem com a UF do login do usuário
                    chunk = chunk[chunk[col_uf_csv].astype(str).str.upper() == uf_usuario]

            if chunk.empty: continue

            # Seleção de colunas limpas
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c), None)
                if encontrada: cols_ok.append(encontrada)
            
            if cols_ok:
                lista_final.append(chunk[list(dict.fromkeys(cols_ok))].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    # --- EXIBIÇÃO FINAL ---
    if df_base.empty:
        st.warning(f"Nenhum dado de 2026 encontrado para a jurisdição: {uf_usuario}")
        return

    # Métricas calculadas sobre o DataFrame já filtrado
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
    # A planilha agora está forçada a mostrar apenas a UF do usuário
    st.dataframe(df_base, use_container_width=True)
