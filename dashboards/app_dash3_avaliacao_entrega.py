import pandas as pd
import sqlite3
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os

#===Caminho do banco===#
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "olist_ecommerce.db")
DB_PATH = os.path.abspath(DB_PATH)
conn = sqlite3.connect(DB_PATH)

#===Consulta SQL: avaliação e tempo de entrega===#
query = """
SELECT 
    r.review_score,
    julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS delivery_time
FROM order_reviews r
JOIN orders o ON r.order_id = o.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
AND r.review_score IS NOT NULL
"""

df = pd.read_sql(query, conn)

#===Inicializando o app Dash===#
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Avaliação vs Tempo de Entrega"

#===Layout do app===#
app.layout = dbc.Container([
    html.H2("Avaliação x Tempo de Entrega", className="my-4 text-center"),
    html.P("Este gráfico mostra a relação entre a nota dada pelos clientes e o tempo de entrega do pedido.", className="mb-4 text-center"),

    #===Slider de filtro por tempo de entrega (em dias)===#
    dcc.RangeSlider(
        id="filtro-tempo",
        min=int(df["delivery_time"].min()),
        max=int(df["delivery_time"].max()),
        value=[0, 30],
        marks={i: f"{i}d" for i in range(0, int(df["delivery_time"].max()) + 1, 5)},
        step=1
    ),

    html.Br(),

    #===Gráfico atualizado dinamicamente com base no slider===#
    dcc.Graph(id="grafico-avaliacao")
], fluid=True)

#===Callback para atualizar o gráfico com base no tempo de entrega===#
@app.callback(
    Output("grafico-avaliacao", "figure"),
    Input("filtro-tempo", "value")
)
def atualizar_grafico(faixa):
    min_dias, max_dias = faixa
    df_filtrado = df[(df["delivery_time"] >= min_dias) & (df["delivery_time"] <= max_dias)]

    #===Agrupando por nota e calculando média de entrega===#
    media_por_nota = df_filtrado.groupby("review_score")["delivery_time"].mean().reset_index()

    #===Gráfico de barras===#
    fig = px.bar(
        media_por_nota,
        x="review_score",
        y="delivery_time",
        text_auto=".1f",
        title=f"Tempo Médio de Entrega por Nota (entre {min_dias} e {max_dias} dias)",
        labels={"review_score": "Nota de Avaliação", "delivery_time": "Tempo Médio de Entrega (dias)"}
    )
    fig.update_layout(template="plotly_white", xaxis=dict(dtick=1))
    return fig

#===Rodando o app===#
if __name__ == "__main__":
    app.run(debug=True)
