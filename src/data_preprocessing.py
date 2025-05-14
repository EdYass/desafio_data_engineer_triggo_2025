#=== Imports principais ===#
import pandas as pd
import sqlite3
import os

#=== Caminho dos dados brutos ===#
raw_path = "../data/raw/"

#=== Mapeamento dos arquivos em um dicionário para facilitar a leitura ===#
file_map = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "product_translation": "product_category_name_translation.csv"
}

#=== Leitura de todos os arquivos CSV com pandas ===#
dfs = {name: pd.read_csv(os.path.join(raw_path, filename)) for name, filename in file_map.items()}

#=== Função para normalizar nomes de colunas ===#
def normalize_columns(df):
    return df.rename(columns=lambda x: x.strip().lower().replace(" ", "_").replace("-", "_"))

#=== Função de limpeza básica ===#
def clean_df(df):
    df = df.drop_duplicates()            #-> Remove duplicatas
    df = df.dropna(how='all')            #-> Remove linhas totalmente vazias
    df = df.dropna(axis=1, how='all')    #-> Remove colunas totalmente vazias
    return df

#=== Aplicando a limpeza e normalização em todos os dataframes ===#
for name in dfs:
    dfs[name] = normalize_columns(dfs[name])
    dfs[name] = clean_df(dfs[name])

#=== Correção de nomes de colunas com erro no dataset de produtos ===#
dfs["products"].rename(columns={
    "product_name_lenght": "product_name_length",
    "product_description_lenght": "product_description_length"
}, inplace=True)

#=== Salvando os dados limpos em CSVs ===#
processed_path = "../data/processed/"
if os.path.exists(processed_path) and not os.path.isdir(processed_path):
    os.remove(processed_path)
os.makedirs(processed_path, exist_ok=True)

for name, df in dfs.items():
    df.to_csv(os.path.join(processed_path, f"{name}.csv"), index=False)

#==========================#
#=== Criação do Banco SQLite ===#
#==========================#

# Caminho e conexão
db_path = os.path.join(processed_path, "olist_ecommerce.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

#=== Criação das tabelas com chaves ===#
cursor.executescript("""
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS order_reviews;
DROP TABLE IF EXISTS order_payments;
DROP TABLE IF EXISTS geolocation;
DROP TABLE IF EXISTS product_translation;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix INTEGER,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city TEXT,
    seller_state TEXT
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_length REAL,
    product_description_length REAL,
    product_photos_qty REAL,
    product_weight_g REAL,
    product_length_cm REAL,
    product_height_cm REAL,
    product_width_cm REAL
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TEXT,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_id TEXT,
    order_item_id INTEGER,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TEXT,
    price REAL,
    freight_value REAL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

CREATE TABLE order_reviews (
    review_id TEXT PRIMARY KEY,
    order_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE order_payments (
    order_id TEXT,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE geolocation (
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat REAL,
    geolocation_lng REAL,
    geolocation_city TEXT,
    geolocation_state TEXT
);

CREATE TABLE product_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
""")

#=== Remoção de duplicatas com base nas chaves primárias antes de inserir no banco ===#
dfs["customers"].drop_duplicates(subset=["customer_id"], inplace=True)
dfs["sellers"].drop_duplicates(subset=["seller_id"], inplace=True)
dfs["products"].drop_duplicates(subset=["product_id"], inplace=True)
dfs["orders"].drop_duplicates(subset=["order_id"], inplace=True)
dfs["order_reviews"].drop_duplicates(subset=["review_id"], inplace=True)
dfs["order_items"].drop_duplicates(subset=["order_id", "order_item_id"], inplace=True)
dfs["product_translation"].drop_duplicates(subset=["product_category_name"], inplace=True)

#=== Inserindo os dados no banco SQLite ===#
for name, df in dfs.items():
    df.to_sql(name, conn, if_exists="append", index=False)

conn.commit()
conn.close()
