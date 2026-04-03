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

    # --- MENU LATERAL ESQUERDO ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Perfil de Acesso")
        nome_display = usuario.get('NOME') or usuario.get('USUARIO') or "Usuário"
        st.info(f"**Login:** {nome_display}")
        
        plano = str(usuario.get('PLANO', 'BRONZE')).upper()
        st.success(f"**Plano:** {plano}")

        locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
        locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]
        
        st.warning(f"📍 **Cidades Base:**\n{', '.join(locais_limpos)}")
        st.divider()

    # CONFIGURAÇÃO DE COLUNAS
    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']
    ver_tudo = "BRASIL" in locais_limpos or plano in ["OURO", "ADMIN", "MASTER"]

    lista_final = []
    ufs_autorizadas = set()
    
    try:
        # 1. Identifica a UF das cidades antes de processar tudo
        if not ver_tudo:
            # Carrega apenas as colunas de localização para identificar a UF
            df_mapeamento = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', usecols=lambda x: any(t in x.upper() for t in ['MUNICI', 'UF']))
            df_mapeamento.columns = [c.upper().strip() for c in df_mapeamento.columns]
            col_m = next((c for c in df_mapeamento.columns if 'MUNICI' in c and 'COD' not in c), None)
            col_u = next((c for c in df_mapeamento.columns if 'UF' in c and 'COD' not in c), None)
            
            if col_m and col_u:
                # Filtra as UFs que possuem as cidades do local_liberado
                ufs_autorizadas = set(df_mapeamento[df_mapeamento[col_m].astype(str).str.upper().isin(locais_limpos)][col_u].unique())

        # 2. Processa a planilha principal com o filtro de UF aplicado
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=85000)
        
        for chunk in reader:
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # Filtro Ano 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # FILTRO DE SEGURANÇA: Bloqueia a planilha por UF
            if not ver_tudo and ufs_autorizadas:
                col_uf_planilha = next((c for c in chunk.columns if c == 'UF' or ('UF' in c and 'COD' not in c)), None)
                if col_uf_planilha:
                    # A planilha só conterá dados dos estados das cidades do local_liberado
                    chunk = chunk[chunk[col_uf_planilha].astype(str).upper().isin(ufs_autorizadas)]

            if chunk.empty: continue

            # Seleção de colunas finais
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c), None)
                if encontrada: cols_ok.append(encontrada)
            
            if cols_ok:
                lista_final.append(chunk[list(dict.fromkeys(cols_ok))].copy())

        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return

    # --- EXIBIÇÃO ---
    if df_base.empty:
        st.warning("Nenhum dado localizado para sua jurisdição em 2026.")
        return

    # Métricas Sincronizadas
    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)
    if col_e:
        v_e = df_base[col_e].apply(limpar_valor).sum()
        m1.metric("Total Empenhado (UF)", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if col_p:
        v_p = df_base[col_p].apply(limpar_valor).sum()
        m2.metric("Total Pago (UF)", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    # Agora a planilha mostrará apenas o Estado (UF) identificado
    st.dataframe(df_base, use_container_width=True)
