import streamlit as st
import pandas as pd
import plotly.express as px

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(
    page_title="Dashboard Contratações Corporativo",
    page_icon="📊",
    layout="wide"
)

# CSS simples
st.markdown("""
    <style>
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #3b82f6 !important;
    }
    .stMultiSelect [data-baseweb="tag"] span {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard de Contratações - Corporativo 2024/2025")
st.markdown("---")

# ================= LOAD DADOS =================
@st.cache_data
def load_data():
    df = pd.read_excel("corporativo.xlsx")

    # Padronizar nomes das colunas
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )

    # Conversão de datas
    date_columns = [
        "DATA ABERTURA DA VAGA",
        "DATA DE FECHAMENTO VAGA EM SELECAO",
        "DATA DE INICIO SUBSTITUICAO",
        "DATA PREFERENCIAL PARA CONTRATACAO"
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                dayfirst=True,
                errors="coerce"
            )

    # Classificação da contratação
    def classificar_contratacao(row):
        motivo = str(row.get("MOTIVO DO DESLIGAMENTO", "")).upper()
        nome = str(row.get("NOME - COLABORADOR", "")).upper()

        if "PROMOCAO" in motivo or "PROMOCAO" in nome:
            return "Promoção"
        elif "AUMENTO DE QUADRO" in motivo or "AUMENTO DE QUADRO" in nome:
            return "Vaga Nova"
        else:
            return "Substituição"

    df["TIPO DE CONTRATACAO"] = df.apply(classificar_contratacao, axis=1)

    # Filtrar anos
    if "ANO" in df.columns:
        df = df[df["ANO"].isin([2024, 2025])]

    # Validação mínima
    obrigatorias = ["ANO", "MES", "FUNCAO", "SUPERINTENDENCIA", "TIPO DE CONTRATACAO"]
    for col in obrigatorias:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente: {col}")

    return df


# ================= EXECUÇÃO =================
try:
    df = load_data()

    # -------- FILTROS --------
    st.sidebar.header("🔍 Filtros")

    anos_sel = st.sidebar.multiselect(
        "Ano",
        sorted(df["ANO"].unique()),
        default=sorted(df["ANO"].unique())
    )

    tipos_sel = st.sidebar.multiselect(
        "Tipo de Contratação",
        df["TIPO DE CONTRATACAO"].unique(),
        default=df["TIPO DE CONTRATACAO"].unique()
    )

    df_filtrado = df[
        (df["ANO"].isin(anos_sel)) &
        (df["TIPO DE CONTRATACAO"].isin(tipos_sel))
    ]

    # -------- KPIs --------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total", len(df_filtrado))
    col2.metric("Vagas Novas", (df_filtrado["TIPO DE CONTRATACAO"] == "Vaga Nova").sum())
    col3.metric("Promoções", (df_filtrado["TIPO DE CONTRATACAO"] == "Promoção").sum())
    col4.metric("Substituições", (df_filtrado["TIPO DE CONTRATACAO"] == "Substituição").sum())

    st.markdown("---")

    palette = ["#1e3a8a", "#3b82f6", "#60a5fa"]

    # -------- GRÁFICOS PRINCIPAIS --------
    col1, col2 = st.columns(2)

    with col1:
        pizza = (
            df_filtrado
            .groupby("TIPO DE CONTRATACAO")
            .size()
            .reset_index(name="Quantidade")
        )

        fig = px.pie(
            pizza,
            values="Quantidade",
            names="TIPO DE CONTRATACAO",
            hole=0.4,
            color_discrete_sequence=palette
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        ano_tipo = (
            df_filtrado
            .groupby(["ANO", "TIPO DE CONTRATACAO"])
            .size()
            .reset_index(name="Quantidade")
        )

        fig = px.bar(
            ano_tipo,
            x="ANO",
            y="Quantidade",
            color="TIPO DE CONTRATACAO",
            barmode="group",
            color_discrete_sequence=palette
        )
        st.plotly_chart(fig, use_container_width=True)

    # -------- VAGAS POR SUPERINTENDÊNCIA --------
    st.markdown("---")
    st.subheader("🏢 Vagas por Superintendência")

    sup_chart = (
        df_filtrado
        .groupby("SUPERINTENDENCIA")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    fig = px.bar(
        sup_chart,
        x="Quantidade",
        y="SUPERINTENDENCIA",
        orientation="h"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    # -------- FUNÇÕES POR SUPERINTENDÊNCIA --------
    st.markdown("---")
    st.subheader("📋 Funções por Superintendência")

    tabela_funcoes = (
        df_filtrado
        .groupby(["SUPERINTENDENCIA", "FUNCAO"])
        .size()
        .reset_index(name="Quantidade")
        .sort_values(["SUPERINTENDENCIA", "Quantidade"], ascending=[True, False])
    )

    st.dataframe(tabela_funcoes, use_container_width=True)

    # -------- TIMELINE --------
    st.markdown("---")
    st.subheader("📅 Timeline de Contratações por Mês")

    df_filtrado["ANO_MES"] = (
        df_filtrado["ANO"].astype(str) + "-" +
        df_filtrado["MES"].astype(int).astype(str).str.zfill(2)
    )

    timeline = (
        df_filtrado
        .groupby(["ANO_MES", "TIPO DE CONTRATACAO"])
        .size()
        .reset_index(name="Quantidade")
        .sort_values("ANO_MES")
    )

    fig = px.line(
        timeline,
        x="ANO_MES",
        y="Quantidade",
        color="TIPO DE CONTRATACAO",
        markers=True,
        color_discrete_sequence=palette
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # -------- TOP CARGOS --------
    st.markdown("---")
    st.subheader("🎯 Top 10 Cargos - Vagas Novas")

    top_cargos = (
        df_filtrado[df_filtrado["TIPO DE CONTRATACAO"] == "Vaga Nova"]
        .groupby("FUNCAO")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
        .head(10)
    )

    fig = px.bar(
        top_cargos,
        x="Quantidade",
        y="FUNCAO",
        orientation="h"
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    # -------- TABELAS --------
    st.markdown("---")
    st.subheader("📋 Detalhamento das Contratações")

    tab1, tab2, tab3 = st.tabs(["Vagas Novas", "Promoções", "Todas"])

    with tab1:
        st.dataframe(
            df_filtrado[df_filtrado["TIPO DE CONTRATACAO"] == "Vaga Nova"]
            [["ANO", "MES", "SUPERINTENDENCIA", "FUNCAO"]],
            use_container_width=True
        )

    with tab2:
        st.dataframe(
            df_filtrado[df_filtrado["TIPO DE CONTRATACAO"] == "Promoção"]
            [["ANO", "MES", "SUPERINTENDENCIA", "FUNCAO", "NOME - COLABORADOR"]],
            use_container_width=True
        )

    with tab3:
        st.dataframe(
            df_filtrado[
                ["ANO", "MES", "SUPERINTENDENCIA", "TIPO DE CONTRATACAO", "FUNCAO", "NOME - COLABORADOR"]
            ],
            use_container_width=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique o arquivo corporativo.xlsx e os nomes das colunas.")
