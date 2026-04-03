import streamlit as st
import pandas as pd
import gdown
import os

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "0"]: 
        return 0.0
    try:
        # Limpeza para cálculo: remove R$, pontos de milhar e ajusta a vírgula decimal
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

    # 1. DOWNLOAD / VERIFICAÇÃO DA BASE
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    usuario = st.session_state.get('usuario_logado')
    if not usuario:
        st.error("Usuário não logado.")
        return

    # --- IDENTIFICAÇÃO NO MENU LATERAL (ESQUERDO) ---
    with st.sidebar:
        st.divider()
        st.markdown("### 👤 Perfil de Acesso")
        nome_display = usuario.get('NOME') or usuario.get('USUARIO') or "Usuário"
        st.info(f"**Login:** {nome_display}")
        
        plano = str(usuario.get('PLANO', 'BRONZE')).upper()
        st.success(f"**Plano:** {plano}")

        # Cidades que o usuário tem direito
        locais_bruto = usuario.get('local_liberado') or usuario.get('LOCAL_LIBERADO') or ""
        locais_limpos = [c.strip().upper() for c in str(locais_bruto).split(',') if c.strip()]
        
        st.warning(f"📍 **Cidades Liberadas:**\n{', '.join(locais_limpos)}")
        st.divider()

    # CONFIGURAÇÃO DE COLUNAS DESEJADAS
    alvos = ['ANO DA EMENDA', 'TIPO DA EMENDA', 'AUTOR', 'MUNICÍPIO', 'UF', 'EMPENHADO', 'LIQUIDADO', 'PAGO']
    
    # Define se o plano permite ver o Brasil todo
    ver_tudo = "BRASIL" in locais_limpos or plano in ["OURO", "ADMIN", "MASTER"]

    lista_final = []
    
    try:
        # Processamento em blocos para não estourar a memória
        reader = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', chunksize=85000)
        
        for chunk in reader:
            # Padroniza nomes das colunas
            chunk.columns = [str(c).upper().strip() for c in chunk.columns]
            
            # FILTRO 1: Ano 2026
            col_ano = next((c for c in chunk.columns if 'ANO' in c), None)
            if col_ano:
                chunk = chunk[chunk[col_ano].astype(str).str.contains('2026', na=False)]
            
            if chunk.empty: continue

            # FILTRO 2: Lógica Estrita de Cidades (Apenas as escolhidas no plano)
            if not ver_tudo:
                col_mun_csv = next((c for c in chunk.columns if 'MUNICI' in c and 'COD' not in c and 'IBGE' not in c), None)
                if col_mun_csv:
                    # Filtra o dataframe para conter APENAS as cidades da lista locais_limpos
                    chunk = chunk[chunk[col_mun_csv].astype(str).str.upper().isin(locais_limpos)]

            if chunk.empty: continue

            # SELEÇÃO DE COLUNAS (Removendo IDs e códigos técnicos)
            cols_ok = []
            for a in alvos:
                encontrada = next((c for c in chunk.columns if a in c and 'COD' not in c and 'IBGE' not in c), None)
                if encontrada:
                    cols_ok.append(encontrada)
            
            if cols_ok:
                # Remove duplicatas de nomes de colunas e anexa à lista
                lista_final.append(chunk[list(dict.fromkeys(cols_ok))].copy())

        # Une todos os blocos filtrados
        df_base = pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

    except Exception as e:
        st.error(f"Erro no processamento dos dados: {e}")
        return

    # --- EXIBIÇÃO NA TELA DA DIREITA ---
    if df_base.empty:
        st.warning(f"Nenhum recurso de 2026 encontrado para: {', '.join(locais_limpos)}")
        return

    # Cálculos para as Métricas do Topo
    col_p = next((c for c in df_base.columns if 'PAGO' in c), None)
    col_e = next((c for c in df_base.columns if 'EMPENHADO' in c), None)

    m1, m2 = st.columns(2)
    
    if col_e:
        v_e = df_base[col_e].apply(limpar_valor).sum()
        m1.metric("Total Empenhado (Cidades Selecionadas)", f"R$ {v_e:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    if col_p:
        v_p = df_base[col_p].apply(limpar_valor).sum()
        m2.metric("Total Pago (Cidades Selecionadas)", f"R$ {v_p:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.markdown("---") 
    
    # Mostra a tabela com as cidades filtradas
    st.dataframe(df_base, use_container_width=True)
