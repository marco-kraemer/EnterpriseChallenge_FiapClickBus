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
from sklearn.metrics import roc_auc_score, precision_score, recall_score, confusion_matrix
import xgboost as xgb

# ============================================
# 1. Conectar ao SQL Server e ler Silver Layer
# ============================================

DRIVER_NAME = "ODBC Driver 17 for SQL Server"
SERVER_NAME = "marco"   # ajuste se necessário (ex: "marco\SQLEXPRESS")
DATABASE_NAME = "EnterpriseChallengeClickBus"

connection_string = f"""
DRIVER={{{DRIVER_NAME}}};
SERVER={SERVER_NAME};
DATABASE={DATABASE_NAME};
Trusted_Connection=yes;
"""

conn = pyodbc.connect(connection_string)
print(">> Conexão bem sucedida.")

# Ler tabela silver.clients_features para DataFrame
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

# Obs: ideal = derivar labels de purchases_clean. Aqui simulamos caso não existam.
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
    np.where(df["segment"] == 0, 0.2, 0)  # bônus para cluster de maior valor
)

print(">> Score de prioridade calculado.")

# ============================================
# 5. Gravar no Gold Layer
# ============================================

# Criar tabela gold.customer_predictions (drop/create)
cursor = conn.cursor()

ddl = """
IF OBJECT_ID('gold.customer_predictions', 'U') IS NOT NULL
    DROP TABLE gold.customer_predictions;

CREATE TABLE gold.customer_predictions (
    customer_id NVARCHAR(128) PRIMARY KEY,
    prob_repurchase_7d DECIMAL(5,4),
    prob_repurchase_30d DECIMAL(5,4),
    segment INT,
    top_destination NVARCHAR(255),
    score_priority DECIMAL(6,4)
);
"""
cursor.execute(ddl)
conn.commit()

# Inserir os dados no Gold
insert_sql = """
INSERT INTO gold.customer_predictions
(customer_id, prob_repurchase_7d, prob_repurchase_30d, segment, top_destination, score_priority)
VALUES (?, ?, ?, ?, ?, ?)
"""

for _, row in df.iterrows():
    cursor.execute(insert_sql, (
        row["customer_id"],
        float(row["prob_repurchase_7d"]),
        float(row["prob_repurchase_30d"]),
        int(row["segment"]),
        row["top_destination"] if row["top_destination"] is not None else None,
        float(row["score_priority"])
    ))

conn.commit()
cursor.close()
conn.close()

print(">> Dados gravados no Gold Layer com sucesso:", df.shape)
