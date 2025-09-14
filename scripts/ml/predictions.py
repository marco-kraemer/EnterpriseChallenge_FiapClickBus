# ============================================
# RoadWise - ClickBus | ML Layer
# Pipeline de Segmentação + Previsão
# ============================================

import pandas as pd
import numpy as np
import pyodbc
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
import xgboost as xgb

# ============================================
# 1. Conectar ao SQL Server e ler Silver Layer
# ============================================

DRIVER_NAME = "ODBC Driver 17 for SQL Server"
SERVER_NAME = "marco"   # ajuste se necessário
DATABASE_NAME = "EnterpriseChallengeClickBus"

connection_string = f"""
DRIVER={{{DRIVER_NAME}}};
SERVER={SERVER_NAME};
DATABASE={DATABASE_NAME};
Trusted_Connection=yes;
"""

conn = pyodbc.connect(connection_string)
print(">> Conexão bem sucedida.")

# Ler tabela silver.clients_features
df = pd.read_sql("SELECT * FROM silver.clients_features;", conn)
print(">> Dados carregados da Silver Layer:", df.shape)

# ============================================
# 2. Segmentação de Clientes (KMeans)
# ============================================

features_cluster = [
    "days_since_last_purchase",
    "purchases_last_90d",
    "ticket_medio",
    "total_purchases_lifetime"
]

X_cluster = df[features_cluster].fillna(0)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_cluster)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
df["segment"] = kmeans.fit_predict(X_scaled)

print(">> Segmentação concluída.")

# ============================================
# 3. Previsão de Recompra (XGBoost)
# ============================================

# Simulação de labels (ideal = derivar de purchases_clean)
if "label_7d" not in df.columns:
    df["label_7d"] = np.random.randint(0, 2, size=len(df))
if "label_30d" not in df.columns:
    df["label_30d"] = np.random.randint(0, 2, size=len(df))

features_ml = [
    "days_since_last_purchase",
    "purchases_last_30d",
    "purchases_last_90d",
    "purchases_last_180d",
    "total_purchases_lifetime",
    "ticket_medio"
]

X = df[features_ml].fillna(0)
y_7d = df["label_7d"]
y_30d = df["label_30d"]

# Modelo 7d
X_train, X_test, y_train, y_test = train_test_split(
    X, y_7d, test_size=0.3, stratify=y_7d, random_state=42
)

model_7d = xgb.XGBClassifier(
    n_estimators=200, learning_rate=0.1, max_depth=5,
    subsample=0.8, colsample_bytree=0.8,
    random_state=42, eval_metric="logloss"
)
model_7d.fit(X_train, y_train)
df["prob_repurchase_7d"] = model_7d.predict_proba(X)[:, 1]

# Modelo 30d
X_train2, X_test2, y_train2, y_test2 = train_test_split(
    X, y_30d, test_size=0.3, stratify=y_30d, random_state=42
)

model_30d = xgb.XGBClassifier(
    n_estimators=200, learning_rate=0.1, max_depth=5,
    subsample=0.8, colsample_bytree=0.8,
    random_state=42, eval_metric="logloss"
)
model_30d.fit(X_train2, y_train2)
df["prob_repurchase_30d"] = model_30d.predict_proba(X)[:, 1]

print(">> Modelos de previsão concluídos.")

# ============================================
# 4. Score de Prioridade
# ============================================

df["score_priority"] = (
    0.6 * df["prob_repurchase_7d"] +
    0.4 * df["prob_repurchase_30d"] +
    np.where(df["segment"] == 0, 0.2, 0)
)

print(">> Score de prioridade calculado.")

# ============================================
# 5. Gravar no Gold Layer (opcional)
# ============================================

cursor = conn.cursor()

ddl = """
IF OBJECT_ID('gold.customer_predictions', 'U') IS NOT NULL
    DROP TABLE gold.customer_predictions;

CREATE TABLE gold.customer_predictions (
    customer_id NVARCHAR(128) PRIMARY KEY,
    last_purchase DATETIME2(0),
    days_since_last_purchase INT,
    purchases_last_30d INT,
    purchases_last_90d INT,
    purchases_last_180d INT,
    total_purchases_lifetime INT,
    ticket_medio DECIMAL(12,2),
    top_destination NVARCHAR(255),
    last_purchase_month TINYINT,
    last_purchase_week TINYINT,
    last_purchase_dayofweek TINYINT,
    last_purchase_period VARCHAR(16),
    prob_repurchase_7d DECIMAL(6,4),
    prob_repurchase_30d DECIMAL(6,4),
    segment INT,
    score_priority DECIMAL(6,4)
);
"""
cursor.execute(ddl)
conn.commit()

insert_sql = """
INSERT INTO gold.customer_predictions
(customer_id, last_purchase, days_since_last_purchase,
 purchases_last_30d, purchases_last_90d, purchases_last_180d,
 total_purchases_lifetime, ticket_medio, top_destination,
 last_purchase_month, last_purchase_week, last_purchase_dayofweek, last_purchase_period,
 prob_repurchase_7d, prob_repurchase_30d, segment, score_priority)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

for _, row in df.iterrows():
    cursor.execute(insert_sql, (
        row["customer_id"],
        row["last_purchase"] if pd.notnull(row["last_purchase"]) else None,
        int(row["days_since_last_purchase"]) if pd.notnull(row["days_since_last_purchase"]) else None,
        int(row["purchases_last_30d"]) if pd.notnull(row["purchases_last_30d"]) else None,
        int(row["purchases_last_90d"]) if pd.notnull(row["purchases_last_90d"]) else None,
        int(row["purchases_last_180d"]) if pd.notnull(row["purchases_last_180d"]) else None,
        int(row["total_purchases_lifetime"]) if pd.notnull(row["total_purchases_lifetime"]) else None,
        float(row["ticket_medio"]) if pd.notnull(row["ticket_medio"]) else None,
        row["top_destination"] if pd.notnull(row["top_destination"]) else None,
        int(row["last_purchase_month"]) if pd.notnull(row["last_purchase_month"]) else None,
        int(row["last_purchase_week"]) if pd.notnull(row["last_purchase_week"]) else None,
        int(row["last_purchase_dayofweek"]) if pd.notnull(row["last_purchase_dayofweek"]) else None,
        row["last_purchase_period"] if pd.notnull(row["last_purchase_period"]) else None,
        float(round(row["prob_repurchase_7d"], 4)) if pd.notnull(row["prob_repurchase_7d"]) else None,
        float(round(row["prob_repurchase_30d"], 4)) if pd.notnull(row["prob_repurchase_30d"]) else None,
        int(row["segment"]) if pd.notnull(row["segment"]) else None,
        float(round(row["score_priority"], 4)) if pd.notnull(row["score_priority"]) else None
    ))

conn.commit()
cursor.close()
conn.close()

print(">> Dados gravados no Gold Layer com sucesso:", df.shape)

# ============================================
# 6. Exportar para CSV (para Streamlit)
# ============================================

df.to_csv("predictions.csv", index=False)
print(">> Arquivo predictions.csv salvo com sucesso:", df.shape)
