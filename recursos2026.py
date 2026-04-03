import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: 
        return 0.0
    try:
        # Padroniza para cálculo: remove R$, espaços e ajusta separadores
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

    # 1. DOWNLOAD DA BASE
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- IDENTIFICAÇÃO DO USUÁRIO NO MENU LATERAL ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Perfil de Acesso")
        
        nome_display = usuario.get('NOME') or usuario.get('USUARIO') or "Usuário"
        st.info(f"**Login:** {nome_display}")
        
        plano_display = str(usuario.get('PLANO', 'BRONZE')).upper()
        st.success(f"**Plano:** {plano_display}")

        tipo_consultor = usuario.get('TIPO_CONSULTOR') or usuario.get('TIPO') or "Não Informado"
        st.warning(f"**Consultor:** {tipo_consultor}")

        locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
        st.write(f"📍 **Permissão:** {locais_bruto}")
        
        st.divider()

    # --- PREPARAÇÃO DOS FILTROS ---
    # Transforma a string "NITERÓI, RIO DE JANEIRO" em uma lista ['NITERÓI', 'RIO DE JANEIRO']
    locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]
    
    # Regra de Visualização Total
    ver_tudo = "BRASIL" in locais_limpos or plano_display in ["OURO", "ADMIN", "MASTER"]

    # Colunas desejadas na tabela
    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']

    lista_final = []
    
    try:
        # Processamento em blocos para performance
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=85000)
        
        for chunk in reader:
            # Padroniza cabeçalhos
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # FILTRO 1: Somente Ano 2026 (Obrigatório para todos)
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty:
                continue

            # FILTRO 2: Segurança por Localidade (Apenas Municípios Liberados)
            if not ver_tudo:
                # Localiza a coluna de Município ignorando códigos IBGE
                col_mun_filtro = next((c for c in chunk.columns if 'MUNICI' in c and 'COD' not in c and 'IBGE' not in c), None)
                if col_mun_filtro:
                    # Cria o padrão de busca (Ex: "NITERÓI|SÃO GONÇALO")
                    padrao_busca = '|'.join(locais_limpos)
                    # Filtra o chunk para manter apenas as linhas onde o Município está na lista liberada
                    chunk = chunk[chunk[col_mun_filtro].astype(str).str.upper().str.contains(padrao_busca, na=False)]

            if chunk.empty:
                continue

            # SELEÇÃO DE COLUNAS (Limpeza visual)
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c and 'ID' not in c), None)
                if encontrada:
                    cols_ok.append(encontrada)
            
            cols_ok = list(dict.fromkeys(cols_ok))
            
            if cols_ok:
                lista_final.append(chunk[cols_ok].copy())

        # Consolida os dados filtrados
        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento de dados: {e}")
        return

    # --- VERIFICAÇÃO FINAL DE DADOS ---
    if df_base.empty:
        st.warning(f"Nenhum registro de 2026 encontrado para sua permissão: {locais_limpos}")
        return

    # --- EXIBIÇÃO DO DASHBOARD ---
    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)

    if col_e:
        v_empenhado = df_base[col_e].apply(limpar_valor).sum()
        m1.metric("Total Empenhado 2026", f"R$ {v_empenhado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    if col_p:
        v_pago = df_base[col_p].apply(limpar_valor).sum()
        m2.metric("Total Pago 2026", f"R$ {v_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    
    # Exibe a tabela filtrada conforme o login e local_liberado
    st.dataframe(df_base, use_container_width=True)
