import pandas as pd
from sqlite3 import connect
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os

#===Conectando ao banco de dados SQLite===#
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "olist_ecommerce.db")
conn = connect(DB_PATH)

#===Consulta SQL para pedidos por mês, estado e categoria===#
query = """
SELECT 
    strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,  -- Agrupa por mês (formato YYYY-MM)
    c.customer_state,
    pt.product_category_name_english AS category,
    COUNT(DISTINCT o.order_id) AS total_orders  -- Conta os pedidos únicos
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN product_translation pt ON p.product_category_name = pt.product_category_name
WHERE o.order_purchase_timestamp IS NOT NULL
GROUP BY order_month, c.customer_state, category
ORDER BY order_month;
"""

#===Carregando os dados no DataFrame===#
df = pd.read_sql(query, conn)

#===Inicializando o app Dash com suporte a múltiplas páginas===#
#->Uso do Bootstrap para melhorar a aparência visual e o suppress_callback_exceptions para permitir callbacks dinâmicos
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Evolução de Vendas - Olist"

#===Layout principal do app===#
# A ideia é deixar o layout limpo: um título, dois filtros e um gráfico abaixo
app.layout = dbc.Container([
    html.H2("Evolução das Vendas - Dashboard Interativo", className="my-4 text-center"),
    html.H5("Filtrar por Estado e Categoria", className="mb-3"),

    #-> Dois dropdowns criados: um para estado e outro para categoria
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="estado-dropdown",
                options=[{"label": estado, "value": estado} for estado in sorted(df["customer_state"].unique())],
                value="SP",  #->Estado inicial selecionado
                clearable=False
            )
        ], md=6),

        dbc.Col([
            dcc.Dropdown(
                id="categoria-dropdown",
                options=[{"label": cat, "value": cat} for cat in sorted(df["category"].dropna().unique())],
                value="bed_bath_table",  #->Categoria inicial selecionada
                clearable=False
            )
        ], md=6)
    ], className="mb-4"),

    #->Aqui o gráfico será atualizado dinamicamente com base nos filtros
    dcc.Graph(id="grafico-vendas")
], fluid=True)

#===Callback para atualizar o gráfico com base nos filtros===#
#->Essa função é chamada toda vez que o usuário muda o dropdown de estado ou categoria
@app.callback(
    Output("grafico-vendas", "figure"),
    Input("estado-dropdown", "value"),
    Input("categoria-dropdown", "value")
)
def atualizar_grafico(estado, categoria):
    #-> Os dados são filtratos com base nas escolhas do usuário
    df_filtrado = df[
        (df["customer_state"] == estado) &
        (df["category"] == categoria)
    ]

    #->Se não houver dados para essa combinação, mostra uma mensagem no gráfico
    if df_filtrado.empty:
        return px.line(title="Sem dados disponíveis para essa combinação.")

    #->Ordena os dados por mês para o gráfico ficar correto
    df_filtrado = df_filtrado.sort_values("order_month")

    #->Gráfico criado com plotly express (gráfico de linha com marcadores nos pontos)
    fig = px.line(
        df_filtrado,
        x="order_month",
        y="total_orders",
        title=f"Evolução de Vendas - {estado} / {categoria}",
        markers=True
    )

    #-> Layout personalizado: título dos eixos e estilo visual
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Total de Pedidos",
        template="plotly_white"
    )
    return fig

#===Rodando o app localmente===#
if __name__ == "__main__":
    app.run(debug=True)
