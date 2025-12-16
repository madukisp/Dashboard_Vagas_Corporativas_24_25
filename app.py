import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Contratações Corporativo",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Contratações - Corporativo 2024/2025")
st.markdown("---")

@st.cache_data
def load_data():
    # leitura local (Streamlit Cloud)
    df = pd.read_excel("corporativo.xlsx")

    df.columns = df.columns.str.strip()

    date_columns = [
        'DATA ABERTURA DA VAGA',
        'DATA DE FECHAMENTO VAGA EM SELEÇÃO',
        'DATA DE INÍCIO SUBSTITUIÇÃO',
        'DATA PREFERENCIAL PARA CONTRATAÇÃO'
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    def classificar_contratacao(row):
        motivo = str(row.get('MOTIVO DO DESLIGAMENTO', '')).upper()
        nome = str(row.get('NOME - COLABORADOR', '')).upper()

        if 'PROMOÇÃO' in motivo or 'PROMOCAO' in motivo or 'PROMOÇÃO' in nome or 'PROMOCAO' in nome:
            return 'Promoção'
        elif 'AUMENTO DE QUADRO' in motivo or 'AUMENTO DE QUADRO' in nome:
            return 'Vaga Nova'
        else:
            return 'Substituição'

    df['Tipo de Contratação'] = df.apply(classificar_contratacao, axis=1)

    df = df[df['Ano'].isin([2024, 2025])]

    return df

try:
    df = load_data()

    st.sidebar.header("🔍 Filtros")

    anos = st.sidebar.multiselect(
        "Ano",
        sorted(df['Ano'].unique()),
        default=sorted(df['Ano'].unique())
    )

    tipos = st.sidebar.multiselect(
        "Tipo de Contratação",
        df['Tipo de Contratação'].unique(),
        default=df['Tipo de Contratação'].unique()
    )

    df_filtrado = df[
        (df['Ano'].isin(anos)) &
        (df['Tipo de Contratação'].isin(tipos))
    ]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", len(df_filtrado))

    with col2:
        st.metric("Vagas Novas", (df_filtrado['Tipo de Contratação'] == 'Vaga Nova').sum())

    with col3:
        st.metric("Promoções", (df_filtrado['Tipo de Contratação'] == 'Promoção').sum())

    with col4:
        st.metric("Substituições", (df_filtrado['Tipo de Contratação'] == 'Substituição').sum())

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        pizza = df_filtrado['Tipo de Contratação'].value_counts().reset_index()
        pizza.columns = ['Tipo', 'Quantidade']

        fig = px.pie(pizza, values='Quantidade', names='Tipo', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        ano_tipo = df_filtrado.groupby(['Ano', 'Tipo de Contratação']).size().reset_index(name='Quantidade')
        fig = px.bar(ano_tipo, x='Ano', y='Quantidade', color='Tipo de Contratação', barmode='group')
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
