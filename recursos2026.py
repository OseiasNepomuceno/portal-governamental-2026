import streamlit as st
import gdown
import pandas as pd
import zipfile
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# --- CONFIGURAÇÃO DE ACESSO ---
# Ele vai buscar o ID_RECURSOS que você salvou no Secrets
FILE_ID = st.secrets["ID_RECURSOS"]
url = f'https://drive.google.com/uc?id={FILE_ID}'
zip_output = 'dados_radar.zip'
extract_path = 'dados_extraidos'

# Atualização: Mensagem personalizada no cache
@st.cache_data(ttl=3600, show_spinner="Aguarde, carregando dados...")
def carregar_dados_drive():
    try:
        if not os.path.exists(zip_output):
            gdown.download(url, zip_output, quiet=True, fuzzy=True)
        with zipfile.ZipFile(zip_output, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        arquivos = os.listdir(extract_path)
        planilha = [f for f in arquivos if f.endswith(('.xlsx', '.csv'))][0]
        caminho_final = os.path.join(extract_path, planilha)
        
        df = pd.read_excel(caminho_final) if planilha.endswith('.xlsx') else pd.read_csv(caminho_final, sep=';', encoding='latin1', low_memory=False)

        # Limpeza de Valores
        def limpar_valor(valor):
            if isinstance(valor, str):
                valor = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            return pd.to_numeric(valor, errors='coerce')

        for col in ['VALOR CONVÊNIO', 'VALOR LIBERADO']:
            if col in df.columns:
                df[col] = df[col].apply(limpar_valor).fillna(0)

        # Filtro Ano 2026
        if 'DATA PUBLICAÇÃO' in df.columns:
            df['DATA PUBLICAÇÃO'] = pd.to_datetime(df['DATA PUBLICAÇÃO'], errors='coerce')
            df = df[df['DATA PUBLICAÇÃO'].dt.year == 2026]
            
        return df
    except Exception as e:
        st.error(f"Erro no carregamento: {e}")
        return None

# --- FUNÇÃO PARA GERAR PDF ---
def gerar_pdf(df_filtrado, cidade):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Relatório Radar de Recursos 2026 - {cidade}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Total de Projetos: {len(df_filtrado)}")
    p.drawString(100, 715, f"Valor Total: R$ {df_filtrado['VALOR CONVÊNIO'].sum():,.2f}")
    
    y = 680
    for i, row in df_filtrado.head(20).iterrows(): 
        p.drawString(100, y, f"- {str(row['OBJETO DO CONVÊNIO'])[:60]}... | R$ {row['VALOR CONVÊNIO']:,.2f}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 750
            
    p.save()
    buffer.seek(0)
    return buffer

# --- INTERFACE PRINCIPAL ---
st.title("🔍 Radar de Recursos 2026")
st.caption("CORE ESSENCE - Consultoria e Estratégia Governamental")

# Atualização: Spinner na interface para garantir o feedback visual
with st.spinner("Aguarde, carregando dados..."):
    df_radar = carregar_dados_drive()

if df_radar is not None:
    # --- FILTROS EM HIERARQUIA ---
    col_uf = 'UF'
    col_mun = 'NOME MUNICÍPIO'
    
    c1, c2 = st.columns(2)
    with c1:
        lista_uf = ["Todos"] + sorted(df_radar[col_uf].dropna().unique().tolist())
        uf_sel = st.selectbox("1. Selecione o Estado (UF):", lista_uf)
    
    df_uf = df_radar.copy()
    if uf_sel != "Todos":
        df_uf = df_radar[df_radar[col_uf] == uf_sel]

    with c2:
        lista_mun = ["Todos"] + sorted(df_uf[col_mun].dropna().unique().tolist())
        mun_sel = st.selectbox("2. Selecione a Cidade:", lista_mun)

    df_final = df_uf.copy()
    if mun_sel != "Todos":
        df_final = df_uf[df_uf[col_mun] == mun_sel]

    # --- INDICADORES ---
    t_conv = float(df_final['VALOR CONVÊNIO'].sum())
    t_lib = float(df_final['VALOR LIBERADO'].sum())
    
    m1, m2, m3 = st.columns(3)
    # Formatação brasileira para as métricas
    m1.metric("Total Convênios", f"R$ {t_conv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    m2.metric("Total Liberado", f"R$ {t_lib:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Projetos", len(df_final))

    # --- 1. GRÁFICO DE DESTINAÇÃO ---
    st.subheader("📊 Destinação de Verbas por Órgão")
    if not df_final.empty:
        destinacao = df_final.groupby('NOME ÓRGÃO SUPERIOR')['VALOR CONVÊNIO'].sum().sort_values(ascending=False).head(10)
        st.bar_chart(destinacao)

    # --- 2. ALERTA DE VIGÊNCIA ---
    st.subheader("⚠️ Alertas de Vigência (Próximos Vencimentos)")
    if 'DATA FINAL VIGÊNCIA' in df_final.columns:
        df_final['DATA FINAL VIGÊNCIA'] = pd.to_datetime(df_final['DATA FINAL VIGÊNCIA'], errors='coerce')
        alertas = df_final.sort_values(by='DATA FINAL VIGÊNCIA').dropna(subset=['DATA FINAL VIGÊNCIA']).head(5)
        st.table(alertas[['OBJETO DO CONVÊNIO', 'DATA FINAL VIGÊNCIA', 'VALOR CONVÊNIO']])

    # --- 3. EXPORTAÇÃO PDF ---
    pdf_file = gerar_pdf(df_final, mun_sel)
    st.download_button(
        label="📥 Baixar Relatório em PDF",
        data=pdf_file,
        file_name=f"Relatorio_Radar_{mun_sel}.pdf",
        mime="application/pdf"
    )

    st.markdown("---")
    st.dataframe(df_final, use_container_width=True)
