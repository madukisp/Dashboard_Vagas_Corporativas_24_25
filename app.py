import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Contratações Corporativo",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Dashboard de Contratações - Corporativo 2024/2025")
st.markdown("---")

@st.cache_data
def load_data():
    df = pd.read_excel(r'\\SERVER-SBCD-RH0\Scripts\Indicadores_Fabiana\corporativo_contratacao_24_25\corporativo.xlsx')
    
    # Padronizar nomes de colunas
    df.columns = df.columns.str.strip()
    
    # Converter datas
    date_columns = ['DATA ABERTURA DA VAGA', 'DATA DE FECHAMENTO VAGA EM SELEÇÃO', 
                    'DATA DE INÍCIO SUBSTITUIÇÃO', 'DATA PREFERENCIAL PARA CONTRATAÇÃO']
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Criar coluna de classificação
    def classificar_contratacao(row):
        motivo = str(row['MOTIVO DO DESLIGAMENTO']).upper() if pd.notna(row['MOTIVO DO DESLIGAMENTO']) else ''
        nome_col = str(row['NOME - COLABORADOR']).upper() if pd.notna(row['NOME - COLABORADOR']) else ''
        
        if 'PROMOÇÃO' in motivo or 'PROMOÇÃO' in nome_col or 'PROMOCAO' in motivo or 'PROMOCAO' in nome_col:
            return 'Promoção'
        elif 'AUMENTO DE QUADRO' in motivo or 'AUMENTO DE QUADRO' in nome_col:
            return 'Vaga Nova'
        else:
            return 'Substituição'
    
    df['Tipo de Contratação'] = df.apply(classificar_contratacao, axis=1)
    
    # Filtrar apenas 2024 e 2025
    df = df[df['Ano'].isin([2024, 2025])]
    
    return df

# Carregar dados
try:
    df = load_data()
    
    # Sidebar - Filtros
    st.sidebar.header("🔍 Filtros")
    
    anos_selecionados = st.sidebar.multiselect(
        "Ano",
        options=sorted(df['Ano'].dropna().unique()),
        default=sorted(df['Ano'].dropna().unique())
    )
    
    tipos_selecionados = st.sidebar.multiselect(
        "Tipo de Contratação",
        options=df['Tipo de Contratação'].unique(),
        default=df['Tipo de Contratação'].unique()
    )
    
    
    # Aplicar filtros
    df_filtrado = df[
        (df['Ano'].isin(anos_selecionados)) &
        (df['Tipo de Contratação'].isin(tipos_selecionados)) 

    ]
    
    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_contratacoes = len(df_filtrado)
        st.metric("Total de Contratações", total_contratacoes)
    
    with col2:
        vagas_novas = len(df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova'])
        st.metric("Vagas Novas", vagas_novas)
    
    with col3:
        promocoes = len(df_filtrado[df_filtrado['Tipo de Contratação'] == 'Promoção'])
        st.metric("Promoções", promocoes)
    
    with col4:
        substituicoes = len(df_filtrado[df_filtrado['Tipo de Contratação'] == 'Substituição'])
        st.metric("Substituições", substituicoes)
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Distribuição por Tipo de Contratação")
        tipo_counts = df_filtrado['Tipo de Contratação'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo', 'Quantidade']
        
        fig_pizza = px.pie(
            tipo_counts,
            values='Quantidade',
            names='Tipo',
            color='Tipo',
            color_discrete_map={
                'Vaga Nova': '#1f77b4',
                'Promoção': '#2ca02c',
                'Substituição': '#ff7f0e'
            },
            hole=0.4
        )
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label+value')
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        st.subheader("📊 Contratações por Ano")
        ano_tipo = df_filtrado.groupby(['Ano', 'Tipo de Contratação']).size().reset_index(name='Quantidade')
        
        fig_bar = px.bar(
            ano_tipo,
            x='Ano',
            y='Quantidade',
            color='Tipo de Contratação',
            barmode='group',
            color_discrete_map={
                'Vaga Nova': '#1f77b4',
                'Promoção': '#2ca02c',
                'Substituição': '#ff7f0e'
            },
            text='Quantidade'
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(xaxis_type='category')
        st.plotly_chart(fig_bar, use_container_width=True)

    # Resumo final
    st.markdown("---")
    st.subheader("📊 Resumo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Período analisado:** {', '.join(map(str, sorted(anos_selecionados)))}
        
        **Total de movimentações:** {total_contratacoes}
        
        **Breakdown:**
        - 🆕 Vagas Novas: {vagas_novas} ({vagas_novas/total_contratacoes*100:.1f}%)
        - ⬆️ Promoções: {promocoes} ({promocoes/total_contratacoes*100:.1f}%)
        - 🔄 Substituições: {substituicoes} ({substituicoes/total_contratacoes*100:.1f}%)
        """)
    
    with col2:
        # Comparação 2024 vs 2025
        if 2024 in anos_selecionados and 2025 in anos_selecionados:
            total_2024 = len(df_filtrado[df_filtrado['Ano'] == 2024])
            total_2025 = len(df_filtrado[df_filtrado['Ano'] == 2025])
            
            if total_2024 > 0:
                variacao = ((total_2025 - total_2024) / total_2024) * 100
                st.markdown(f"""
                **Comparação 2024 vs 2025:**
                - 2024: {total_2024} contratações
                - 2025: {total_2025} contratações
                - Variação: {variacao:+.1f}%
                """)
    
    # Timeline mensal
    st.markdown("---")
    st.subheader("📅 Timeline de Contratações por Mês")
    
    df_timeline = df_filtrado.copy()
    df_timeline['Ano-Mês'] = df_timeline['Ano'].astype(str) + '-' + df_timeline['Mês'].astype(str).str.zfill(2)
    
    timeline = df_timeline.groupby(['Ano-Mês', 'Tipo de Contratação']).size().reset_index(name='Quantidade')
    timeline = timeline.sort_values('Ano-Mês')
    
    fig_linha = px.line(
        timeline,
        x='Ano-Mês',
        y='Quantidade',
        color='Tipo de Contratação',
        markers=True,
        color_discrete_map={
            'Vaga Nova': '#1f77b4',
            'Promoção': '#2ca02c',
            'Substituição': '#ff7f0e'
        }
    )
    fig_linha.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_linha, use_container_width=True)
    
    # Top cargos
    st.markdown("---")
    col1 = st.columns(1)[0]
    
    with col1:
        st.subheader("🎯 Top 10 Cargos - Vagas Novas")
        vagas_novas_df = df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova']
        top_cargos_novas = vagas_novas_df['FUNÇÃO'].value_counts().head(10).reset_index()
        top_cargos_novas.columns = ['Cargo', 'Quantidade']
        
        fig_bar_novas = px.bar(
            top_cargos_novas,
            x='Quantidade',
            y='Cargo',
            orientation='h',
            color='Quantidade',
            color_continuous_scale='Blues'
        )
        fig_bar_novas.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar_novas, use_container_width=True)
    

    

    
    # Tabela detalhada
    st.markdown("---")
    st.subheader("📋 Detalhamento das Contratações")
    
    # Criar tabs para cada tipo
    tab1, tab2, tab3 = st.tabs(["Vagas Novas", "Promoções", "Todas"])
    
    with tab1:
        st.dataframe(
            df_filtrado[df_filtrado['Tipo de Contratação'] == 'Vaga Nova'][
                ['Ano', 'Mês', 'FUNÇÃO']
            ].reset_index(drop=True),
            use_container_width=True
        )
    
    with tab2:
        st.dataframe(
            df_filtrado[df_filtrado['Tipo de Contratação'] == 'Promoção'][
                ['Ano', 'Mês', 'FUNÇÃO', 'NOME - COLABORADOR']
            ].reset_index(drop=True),
            use_container_width=True
        )
    
    with tab3:
        st.dataframe(
            df_filtrado[
                ['Ano', 'Mês', 'Tipo de Contratação', 'FUNÇÃO', 'NOME - COLABORADOR']
            ].reset_index(drop=True),
            use_container_width=True
        )
    


except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.info("Verifique se o arquivo está no formato correto.")