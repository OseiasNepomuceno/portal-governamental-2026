def exibir_radar():
    """Esta função desenha o Radar com mapeamento específico para a base de Favorecidos"""
    st.title("🏛️ Radar de Emendas Parlamentares")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        fonte_sel = st.selectbox("Base de Dados:", list(FONTES_DADOS.keys()))
    with col_f2:
        ano_sel = st.selectbox("Ano de Referência", [2026, 2025, 2024], index=0)
    with col_f3:
        mes_sel = "Todos"
        if fonte_sel != "Visão Geral (Emendas)":
            meses = ["Todos", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
            mes_sel = st.selectbox("Mês de Referência (Número)", meses)

    id_chave = FONTES_DADOS[fonte_sel]
    with st.spinner("🛰️ Sincronizando dados estratégicos..."):
        df_base, msg = carregar_dados_drive(id_chave)
    
    if df_base is not None:
        # --- MAPEAMENTO COM OS NOMES REAIS QUE VOCÊ ENVIOU ---
        col_v_emp = achar(df_base, ["VALOR", "RECEBIDO"]) or \
                    achar(df_base, ["VALOR", "EMPENHADO"]) or \
                    achar(df_base, ["VALOR", "REPASSE"])
        
        col_v_pag = achar(df_base, ["VALOR", "PAGO"]) or col_v_emp # Se não tiver 'pago', usa o 'recebido'
        
        col_autor = achar(df_base, ["NOME", "AUTOR"]) or achar(df_base, ["PARLAMENTAR"])
        
        col_dest  = achar(df_base, ["FAVORECIDO"]) or \
                    achar(df_base, ["MUNICÍPIO"]) or \
                    achar(df_base, ["BENEFICIARIO"])

        col_tempo = achar(df_base, ["ANO", "MÊS"]) or achar(df_base, ["ANO"])
        
        if col_v_emp:
            # Limpeza Numérica
            df_base[col_v_emp] = df_base[col_v_emp].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_base[col_v_emp] = pd.to_numeric(df_base[col_v_emp], errors='coerce').fillna(0)

            # --- LÓGICA PARA A COLUNA 'ANO/MÊS' ---
            df_final = df_base
            if col_tempo:
                # Filtra pelo Ano (ex: Procura "2026" dentro de "2026/03")
                df_final = df_base[df_base[col_tempo].astype(str).str.contains(str(ano_sel))]
                
                # Filtra pelo Mês se selecionado (ex: Procura "/03" dentro de "2026/03")
                if mes_sel != "Todos":
                    df_final = df_final[df_final[col_tempo].astype(str).str.contains(f"/{mes_sel}")]

            # --- CARDS DE INDICADORES ---
            v_total_periodo = df_final[col_v_emp].sum()
            
            k1, k2, k3 = st.columns(3)
            label_t = "no Ano" if mes_sel == "Todos" else f"em {mes_sel}/{ano_sel}"
            
            k1.metric(f"Total Identificado {label_t}", formatar_brl(v_total_periodo))
            k2.metric("Qtd. de Repasses", f"{len(df_final)} itens")
            k3.metric("Média por Registro", formatar_brl(v_total_periodo / len(df_final) if len(df_final) > 0 else 0))

            st.markdown("---")

            if not df_final.empty:
                g1, g2 = st.columns(2)
                with g1:
                    st.write("📈 **Ranking de Origem (Autores)**")
                    if col_autor:
                        st.bar_chart(df_final.groupby(col_autor)[col_v_emp].sum().sort_values(ascending=False).head(10))
                with g2:
                    st.write("📍 **Principais Destinos (Favorecidos)**")
                    if col_dest:
                        st.bar_chart(df_final.groupby(col_dest)[col_v_emp].sum().sort_values(ascending=False).head(10))

                st.write("### 🔍 Detalhamento dos Recebimentos")
                st.dataframe(df_final, use_container_width=True)
            else:
                st.warning(f"Nenhum dado encontrado para {mes_sel}/{ano_sel}.")
        else:
            st.error(f"⚠️ Coluna de Valor não encontrada. Colunas: {list(df_base.columns)}")
    else:
        st.error(msg)
