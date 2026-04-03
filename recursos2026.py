import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: 
        return 0.0
    try:
        # Formatação para cálculo (R$ 1.000,00 -> 1000.00)
        v = str(v).upper().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        return float(v)
    except: 
        return 0.0

def exibir_recursos():
    st.title("📊 Radar de Recursos 2026")
    
    file_id = st.secrets.get("file_id_convenios")
    nome_arquivo = "20260320_Convenios.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando Base de Dados Nacional..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- LÓGICA DE PRODUTO (BÁSICO VS PREMIUM) ---
    plano = str(usuario.get('PLANO', 'BÁSICO')).upper()
    uf_escolhida = str(usuario.get('UF_LIBERADA') or "").strip().upper()

    # Define a abrangência total se for PREMIUM ou se a UF for BRASIL
    acesso_nacional = (plano == "PREMIUM" or uf_escolhida == "BRASIL")

    # --- MENU LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Área do Consultor")
        st.info(f"**Consultor:** {usuario.get('NOME') or 'Usuário'}")
        
        if acesso_nacional:
            st.success("✅ **Plano:** PREMIUM (Nacional)")
            st.caption("Acesso total a todos os estados do Brasil.")
        else:
            st.warning(f"💼 **Plano:** BÁSICO (Estadual)")
            st.write(f"📍 **Jurisdição:** {uf_escolhida}")
        st.divider()

    # Colunas que queremos exibir na tabela
    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']
    lista_final = []
    
    try:
        # Leitura otimizada por blocos (chunks)
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=100000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # 1. FILTRO POR ANO (Sempre 2026)
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # 2. FILTRO DE ACESSO (Se não for nacional, trava na UF do consultor)
            if not acesso_nacional and uf_escolhida:
                col_uf_csv = next((c for c in chunk.columns if c == 'UF' or (len(c) == 2 and 'UF' in c)), None)
                if col_uf_csv:
                    chunk = chunk[chunk[col_uf_csv].astype(str).str.upper() == uf_escolhida]

            if chunk.empty: continue

            # 3. SELEÇÃO DE COLUNAS ÚTEIS
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c), None)
                if encontrada: cols_ok.append(encontrada)
            
            if cols_ok:
                lista_final.append(chunk[list(dict.fromkeys(cols_ok))].copy())

        # Consolidação da tabela final
        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return

    # --- TELA PRINCIPAL (DASHBOARD) ---
    if df_base.empty:
        st.warning(f"Sem dados para {'o Brasil' if acesso_nacional else uf_escolhida} em 2026.")
        return

    # Mapeamento de colunas financeiras
    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)
    label_regiao = "Brasil" if acesso_nacional else uf_escolhida
    
    if col_e:
        v_e = df_base[col_e].apply(limpar_valor).sum()
        m1.metric(f"Total Empenhado ({label_regiao})", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if col_p:
        v_p = df_base[col_p].apply(limpar_valor).sum()
        m2.metric(f"Total Pago ({label_regiao})", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    
    # Exibição da planilha (travada conforme o plano)
    st.dataframe(df_base, use_container_width=True)
