USE EnterpriseChallengeClickBus;
GO

/* ==========================================================
   0. Carga do Silver (sempre antes dos testes)
   ========================================================== */
EXEC silver.load_silver;
GO

/* ==========================================================
   1. Variáveis auxiliares (mesma lógica da procedure)
   ========================================================== */
DECLARE @today DATE = (SELECT CAST(MAX(purchase_datetime) AS DATE) FROM silver.purchases_clean);
DECLARE @cut30  DATETIME2(0) = DATEADD(DAY, -30,  @today);
DECLARE @cut90  DATETIME2(0) = DATEADD(DAY, -90,  @today);
DECLARE @cut180 DATETIME2(0) = DATEADD(DAY, -180, @today);

--------------------------------------------------------------
-- TESTE 1 - Contagem de linhas entre Bronze e Silver
--------------------------------------------------------------
SELECT 
    (SELECT COUNT(*) FROM bronze.df_t) AS bronze_rows,
    (SELECT COUNT(*) FROM silver.purchases_clean) AS silver_rows;
/* Esperado: silver_rows <= bronze_rows */

--------------------------------------------------------------
-- TESTE 2 - Clientes únicos
--------------------------------------------------------------
SELECT 
    (SELECT COUNT(DISTINCT customer_id) FROM silver.purchases_clean) AS clientes_clean,
    (SELECT COUNT(*) FROM silver.clients_features) AS clientes_features;
/* Esperado: clientes_clean = clientes_features */

--------------------------------------------------------------
-- TESTE 3 - Última compra por cliente
--------------------------------------------------------------
SELECT cf.customer_id, cf.last_purchase, MAX(pc.purchase_datetime) AS expected_last_purchase
FROM silver.clients_features cf
JOIN silver.purchases_clean pc ON pc.customer_id = cf.customer_id
GROUP BY cf.customer_id, cf.last_purchase
HAVING cf.last_purchase <> MAX(pc.purchase_datetime);
/* Esperado: 0 linhas */

--------------------------------------------------------------
-- TESTE 4 - Dias desde última compra
--------------------------------------------------------------
SELECT TOP 20
    cf.customer_id,
    cf.days_since_last_purchase,
    DATEDIFF(DAY, cf.last_purchase, @today) AS expected_days
FROM silver.clients_features cf
WHERE cf.days_since_last_purchase <> DATEDIFF(DAY, cf.last_purchase, @today);
/* Esperado: 0 linhas */

--------------------------------------------------------------
-- TESTE 5 - Compras últimos 30/90/180 dias
--------------------------------------------------------------
-- 30 dias
SELECT cf.customer_id, cf.purchases_last_30d, COUNT(*) AS expected_last_30d
FROM silver.clients_features cf
JOIN silver.purchases_clean pc ON cf.customer_id = pc.customer_id
WHERE pc.purchase_datetime > @cut30
GROUP BY cf.customer_id, cf.purchases_last_30d
HAVING cf.purchases_last_30d <> COUNT(*);

-- 90 dias
SELECT cf.customer_id, cf.purchases_last_90d, COUNT(*) AS expected_last_90d
FROM silver.clients_features cf
JOIN silver.purchases_clean pc ON cf.customer_id = pc.customer_id
WHERE pc.purchase_datetime > @cut90
GROUP BY cf.customer_id, cf.purchases_last_90d
HAVING cf.purchases_last_90d <> COUNT(*);

-- 180 dias
SELECT cf.customer_id, cf.purchases_last_180d, COUNT(*) AS expected_last_180d
FROM silver.clients_features cf
JOIN silver.purchases_clean pc ON cf.customer_id = pc.customer_id
WHERE pc.purchase_datetime > @cut180
GROUP BY cf.customer_id, cf.purchases_last_180d
HAVING cf.purchases_last_180d <> COUNT(*);
/* Esperado: 0 linhas em todos os blocos */

--------------------------------------------------------------
-- TESTE 6 - Total lifetime
--------------------------------------------------------------
SELECT cf.customer_id, cf.total_purchases_lifetime, COUNT(*) AS expected_total
FROM silver.clients_features cf
JOIN silver.purchases_clean pc ON cf.customer_id = pc.customer_id
GROUP BY cf.customer_id, cf.total_purchases_lifetime
HAVING cf.total_purchases_lifetime <> COUNT(*);
/* Esperado: 0 linhas */

--------------------------------------------------------------
-- TESTE 7 - Top Destination
--------------------------------------------------------------
WITH ranked_dest AS (
    SELECT customer_id, place_destination_departure,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id
               ORDER BY COUNT(*) DESC, MAX(purchase_datetime) DESC
           ) AS rn
    FROM silver.purchases_clean
    GROUP BY customer_id, place_destination_departure
)
SELECT cf.customer_id, cf.top_destination, rd.place_destination_departure AS expected_top_dest
FROM silver.clients_features cf
JOIN ranked_dest rd ON cf.customer_id = rd.customer_id AND rd.rn = 1
WHERE cf.top_destination <> rd.place_destination_departure;
/* Esperado: 0 linhas */

--------------------------------------------------------------
-- TESTE 8 - Ticket médio
--------------------------------------------------------------
SELECT cf.customer_id, cf.ticket_medio, AVG(pc.gmv_success) AS expected_ticket_medio
FROM silver.clients_features cf
JOIN silver.purchases_clean pc ON pc.customer_id = cf.customer_id
GROUP BY cf.customer_id, cf.ticket_medio
HAVING cf.ticket_medio <> AVG(pc.gmv_success);
/* Esperado: 0 linhas */

--------------------------------------------------------------
-- TESTE 9 - Sanidade das colunas derivadas
--------------------------------------------------------------
SELECT 
    MIN(purchase_month) AS min_month, MAX(purchase_month) AS max_month,
    MIN(purchase_week) AS min_week, MAX(purchase_week) AS max_week,
    MIN(purchase_dayofweek) AS min_day, MAX(purchase_dayofweek) AS max_day
FROM silver.purchases_clean;
/* Esperado:
   min_month >= 1 e max_month <= 12
   min_week >= 1 e max_week <= 53
   min_day >= 1 e max_day <= 7 */

--------------------------------------------------------------
-- TESTE 10 - GMV e Tickets
--------------------------------------------------------------
SELECT * 
FROM silver.purchases_clean 
WHERE gmv_success < 0 OR total_tickets_qty < 0;
/* Esperado: 0 linhas */

--------------------------------------------------------------
-- AMOSTRAS DE DADOS PARA INSPEÇÃO
--------------------------------------------------------------
SELECT TOP 50
    customer_id,
    purchase_datetime,
    place_origin_departure,
    place_destination_departure,
    gmv_success,
    total_tickets_qty,
    purchase_month,
    purchase_week,
    purchase_dayofweek,
    purchase_period
FROM silver.purchases_clean
ORDER BY customer_id, purchase_datetime;

SELECT TOP 50
    customer_id,
    last_purchase,
    days_since_last_purchase,
    purchases_last_30d,
    purchases_last_90d,
    purchases_last_180d,
    total_purchases_lifetime,
    top_destination,
    last_purchase_month,
    last_purchase_week,
    last_purchase_dayofweek,
    last_purchase_period,
    ticket_medio
FROM silver.clients_features
ORDER BY customer_id;
