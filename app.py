import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard Contratações Corporativo",
    page_icon="📊",
    layout="wide"
)

# CSS customizado para os filtros
st.markdown("""
    <style>
    /* Mudar cor dos badges dos multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #3b82f6 !important;
    }
    
    /* Ajustar texto dos badges */
    .stMultiSelect [data-baseweb="tag"] span {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

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

    col1.metric("Total", len(df_filtrado))
    col2.metric("Vagas Novas", (df_filtrado['Tipo de Contratação'] == 'Vaga Nova').sum())
    col3.metric("Promoções", (df_filtrado['Tipo de Contratação'] == 'Promoção').sum())
    col4.metric("Substituições", (df_filtrado['Tipo de Contratação'] == 'Substituição').sum())

    st.markdown("---")

    # Paleta de tons de azul em degradê
    color_palette = ['#1e3a8a', '#3b82f6', '#60a5fa']

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        pizza = df_filtrado['Tipo de Contratação'].value_counts().reset_index()
        pizza.columns = ['Tipo', 'Quantidade']
        fig = px.pie(
            pizza, 
            values='Quantidade', 
            names='Tipo', 
            hole=0.4,
            color_discrete_sequence=color_palette
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            showlegend=True,
            font=dict(size=12),
            margin=dict(t=30, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        ano_tipo = (
            df_filtrado
            .groupby(['Ano', 'Tipo de Contratação'])
            .size()
            .reset_index(name='Quantidade')
        )
        fig = px.bar(
            ano_tipo,
            x='Ano',
            y='Quantidade',
            color='Tipo de Contratação',
            barmode='group',
            color_discrete_sequence=color_palette
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            margin=dict(t=30, b=30),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        )
        st.plotly_chart(fig, use_container_width=True)

    # 🔹 VAGAS POR SUPERINTENDÊNCIA
    st.markdown("---")
    st.subheader("🏢 Vagas por Superintendência")

    sup_chart = (
        df_filtrado
        .groupby('SUPERINTENDENCIA')
        .size()
        .reset_index(name='Quantidade')
        .sort_values('Quantidade', ascending=False)
    )

    fig = px.bar(
        sup_chart,
        x='Quantidade',
        y='SUPERINTENDENCIA',
        orientation='h',
        color='Quantidade',
        color_continuous_scale=['#dbeafe', '#3b82f6', '#1e3a8a']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(t=30, b=30),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(categoryorder='total ascending', showgrid=False),
        showlegend=False
    )
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # 🔹 FUNÇÕES POR SUPERINTENDÊNCIA (TABELA)
    st.markdown("---")
    st.subheader("📋 Funções por Superintendência")

    tabela_funcoes = (
        df_filtrado
        .groupby(['SUPERINTENDENCIA', 'FUNÇÃO'])
        .size()
        .reset_index(name='Quantidade')
        .sort_values(['SUPERINTENDENCIA', 'Quantidade'], ascending=[True, False])
    )

    st.dataframe(
        tabela_funcoes,
        use_container_width=True
    )


    # Timeline
    st.markdown("---")
    st.subheader("📅 Timeline de Contratações por Mês")

    df_filtrado['Ano-Mês'] = (
        df_filtrado['Ano'].astype(str) + '-' +
        df_filtrado['Mês'].astype(int).astype(str).str.zfill(2)
    )

    timeline = (
        df_filtrado
        .groupby(['Ano-Mês', 'Tipo de Contratação'])
        .size()
        .reset_index(name='Quantidade')
        .sort_values('Ano-Mês')
    )

    fig = px.line(
        timeline,
        x='Ano-Mês',
        y='Quantidade',
        color='Tipo de Contratação',
        markers=True,
        color_discrete_sequence=color_palette
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(t=30, b=30),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    )
    fig.update_traces(line=dict(width=3))
    st.plotly_chart(fig, use_container_width=True)

    # Top cargos
    st.markdown("---")
    st.subheader("🎯 Top 10 Cargos - Vagas Novas")

    vagas_novas_df = df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova']
    top_cargos = vagas_novas_df['FUNÇÃO'].value_counts().head(10).reset_index()
    top_cargos.columns = ['Cargo', 'Quantidade']

    fig = px.bar(
        top_cargos, 
        x='Quantidade', 
        y='Cargo', 
        orientation='h',
        color='Quantidade',
        color_continuous_scale=['#dbeafe', '#3b82f6', '#1e3a8a']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(t=30, b=30),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(categoryorder='total ascending', showgrid=False),
        showlegend=False
    )
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # Tabelas
    st.markdown("---")
    st.subheader("📋 Detalhamento das Contratações")

    tab1, tab2, tab3 = st.tabs(["Vagas Novas", "Promoções", "Todas"])

    with tab1:
        st.dataframe(
            df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova']
            [['Ano', 'Mês', 'SUPERINTENDENCIA', 'FUNÇÃO']],
            use_container_width=True
        )

    with tab2:
        st.dataframe(
            df_filtrado[df_filtrado['Tipo de Contratação'] == 'Promoção']
            [['Ano', 'Mês', 'SUPERINTENDENCIA', 'FUNÇÃO', 'NOME - COLABORADOR']],
            use_container_width=True
        )

    with tab3:
        st.dataframe(
            df_filtrado[['Ano', 'Mês', 'SUPERINTENDENCIA', 'Tipo de Contratação', 'FUNÇÃO', 'NOME - COLABORADOR']],
            use_container_width=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se o arquivo corporativo.xlsx está no repositório.")