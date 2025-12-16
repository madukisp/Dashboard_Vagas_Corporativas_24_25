import streamlit as st
import pandas as pd
import plotly.express as px

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
    df = pd.read_excel("corporativo.xlsx")

    # Padronizar nomes de colunas
    df.columns = df.columns.str.strip()

    # Converter datas
    date_columns = [
        'DATA ABERTURA DA VAGA',
        'DATA DE FECHAMENTO VAGA EM SELEÇÃO',
        'DATA DE INÍCIO SUBSTITUIÇÃO',
        'DATA PREFERENCIAL PARA CONTRATAÇÃO'
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Classificação
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

    # Filtrar apenas 2024 e 2025
    if 'Ano' in df.columns:
        df = df[df['Ano'].isin([2024, 2025])]

    return df


try:
    df = load_data()

    st.sidebar.header("🔍 Filtros")

    anos_selecionados = st.sidebar.multiselect(
        "Ano",
        sorted(df['Ano'].dropna().unique()),
        default=sorted(df['Ano'].dropna().unique())
    )

    tipos_selecionados = st.sidebar.multiselect(
        "Tipo de Contratação",
        df['Tipo de Contratação'].unique(),
        default=df['Tipo de Contratação'].unique()
    )

    df_filtrado = df[
        (df['Ano'].isin(anos_selecionados)) &
        (df['Tipo de Contratação'].isin(tipos_selecionados))
    ]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    total_contratacoes = len(df_filtrado)
    vagas_novas = (df_filtrado['Tipo de Contratação'] == 'Vaga Nova').sum()
    promocoes = (df_filtrado['Tipo de Contratação'] == 'Promoção').sum()
    substituicoes = (df_filtrado['Tipo de Contratação'] == 'Substituição').sum()

    col1.metric("Total", total_contratacoes)
    col2.metric("Vagas Novas", vagas_novas)
    col3.metric("Promoções", promocoes)
    col4.metric("Substituições", substituicoes)

    st.markdown("---")

    # Gráficos
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

    # Timeline
    st.markdown("---")
    st.subheader("📅 Timeline de Contratações por Mês")

    df_filtrado['Ano-Mês'] = (
        df_filtrado['Ano'].astype(str) + '-' +
        df_filtrado['Mês'].astype(int).astype(str).str.zfill(2)
    )

    timeline = df_filtrado.groupby(['Ano-Mês', 'Tipo de Contratação']).size().reset_index(name='Quantidade')
    timeline = timeline.sort_values('Ano-Mês')

    fig = px.line(timeline, x='Ano-Mês', y='Quantidade', color='Tipo de Contratação', markers=True)
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Top cargos
    st.markdown("---")
    st.subheader("🎯 Top 10 Cargos - Vagas Novas")

    vagas_novas_df = df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova']
    top_cargos = vagas_novas_df['FUNÇÃO'].value_counts().head(10).reset_index()
    top_cargos.columns = ['Cargo', 'Quantidade']

    fig = px.bar(top_cargos, x='Quantidade', y='Cargo', orientation='h')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

    # Tabelas
    st.markdown("---")
    st.subheader("📋 Detalhamento das Contratações")

    tab1, tab2, tab3 = st.tabs(["Vagas Novas", "Promoções", "Todas"])

    with tab1:
        st.dataframe(
            df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova'][['Ano', 'Mês', 'FUNÇÃO']],
            use_container_width=True
        )

    with tab2:
        st.dataframe(
            df_filtrado[df_filtrado['Tipo de Contratação'] == 'Promoção'][['Ano', 'Mês', 'FUNÇÃO', 'NOME - COLABORADOR']],
            use_container_width=True
        )

    with tab3:
        st.dataframe(
            df_filtrado[['Ano', 'Mês', 'Tipo de Contratação', 'FUNÇÃO', 'NOME - COLABORADOR']],
            use_container_width=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se o arquivo corporativo.xlsx está no repositório.")
