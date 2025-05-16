import pandas as pd
import sqlite3
import plotly.express as px
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import os
import json

#===Caminho do banco===#
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "olist_ecommerce.db")
DB_PATH = os.path.abspath(DB_PATH)
conn = sqlite3.connect(DB_PATH)

#===Caminho do GeoJSON===#
GEO_PATH = os.path.join(os.path.dirname(__file__), "geojson", "brazil_states.geojson")
GEO_PATH = os.path.abspath(GEO_PATH)

#===Carregando o GeoJSON===#
with open(GEO_PATH, "r", encoding="utf-8") as f:
    brazil_geo = json.load(f)

#===Consulta SQL: total de pedidos por estado===#
query = """
SELECT 
    c.customer_state AS state,
    COUNT(DISTINCT o.order_id) AS total_orders
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_state
"""
df_estado = pd.read_sql(query, conn)

#===Conversão opcional de siglas para nomes===#
#->Necessário se o GeoJSON usar nomes completos como "São Paulo" em vez de "SP"
sigla_to_nome = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins"
}
df_estado["state_name"] = df_estado["state"].map(sigla_to_nome)

#===Inicializando o app Dash===#
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Mapa de Vendas por Estado"

#===Layout do app===#
app.layout = dbc.Container([
    html.H2("Mapa de Vendas por Estado", className="my-4 text-center"),
    html.P("Este gráfico mostra o total de pedidos por estado brasileiro, com base nos dados do e-commerce.",
           className="mb-4 text-center"),
    
    dcc.Graph(
        id="mapa-vendas",
        figure=px.choropleth(
            df_estado,
            geojson=brazil_geo,
            locations="state_name",                #->Nome do estado no DataFrame
            featureidkey="properties.name",        #->Nome do estado no GeoJSON
            color="total_orders",
            color_continuous_scale="Blues",
            title="Concentração de Pedidos por Estado"
        ).update_geos(fitbounds="locations", visible=False).update_layout(template="plotly_white")
    )
], fluid=True)

#===Rodando o app===#
if __name__ == "__main__":
    app.run(debug=True)
