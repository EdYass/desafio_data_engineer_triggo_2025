import pandas as pd
import sqlite3
import plotly.express as px
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import os

#===Caminho do banco===#
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "olist_ecommerce.db")
DB_PATH = os.path.abspath(DB_PATH)
conn = sqlite3.connect(DB_PATH)

#===Consulta SQL: métricas dos vendedores===#
query = """
SELECT 
    s.seller_id,
    COUNT(DISTINCT o.order_id) AS total_orders,
    AVG(r.review_score) AS avg_score,
    AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_delivery_time
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY s.seller_id
HAVING total_orders >= 50
"""

#-> Apenas vendedores com no mínimo 50 pedidos

#===Carregando os dados===#
df = pd.read_sql(query, conn)

#===Inicializando o app Dash===#
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Desempenho dos Vendedores"

#===Layout do app===#
app.layout = dbc.Container([
    html.H2("Desempenho dos Vendedores", className="my-4 text-center"),
    html.P("Este painel mostra os vendedores com melhor desempenho com base em nota média, tempo de entrega e volume de pedidos.",
           className="mb-4 text-center"),

    # Dropdown para selecionar métrica
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="filtro-metrica",
                options=[
                    {"label": "Nota Média", "value": "avg_score"},
                    {"label": "Tempo Médio de Entrega", "value": "avg_delivery_time"},
                    {"label": "Volume de Pedidos", "value": "total_orders"}
                ],
                value="avg_score",
                clearable=False
            )
        ], md=6)
    ], className="mb-4"),

    dcc.Graph(id="grafico-vendedores")
], fluid=True)

#===Callback para atualizar gráfico conforme métrica selecionada===#
@app.callback(
    dash.Output("grafico-vendedores", "figure"),
    dash.Input("filtro-metrica", "value")
)
def atualizar_grafico(metrica):
    #===Ordena os top 10 vendedores de acordo com a métrica escolhida===#
    df_top = df.sort_values(by=metrica, ascending=(metrica != "total_orders")).head(10)

    titulo_map = {
        "avg_score": "Nota Média",
        "avg_delivery_time": "Tempo Médio de Entrega (dias)",
        "total_orders": "Total de Pedidos"
    }

    fig = px.bar(
        df_top,
        x=metrica,
        y="seller_id",
        orientation="h",
        title=f"Top 10 Vendedores por {titulo_map[metrica]}",
        labels={"seller_id": "Vendedor", metrica: titulo_map[metrica]},
        text_auto=".2f"
    )
    fig.update_layout(template="plotly_white", yaxis=dict(autorange="reversed"))
    return fig

#===Rodando o app===#
if __name__ == "__main__":
    app.run(debug=True)
