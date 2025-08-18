CREATE OR ALTER PROCEDURE silver.load_silver AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        TRUNCATE TABLE silver.purchases_clean;
        TRUNCATE TABLE silver.clients_features;

        ;WITH base AS (
            SELECT
                LTRIM(RTRIM(fk_contact)) AS customer_id,
                TRY_CONVERT(DATETIME2(0), CONCAT(date_purchase, ' ', time_purchase), 120) AS purchase_datetime,
                NULLIF(LTRIM(RTRIM(place_origin_departure)), '0') AS place_origin_departure,
                NULLIF(LTRIM(RTRIM(place_destination_departure)), '0') AS place_destination_departure,
                NULLIF(LTRIM(RTRIM(place_origin_return)), '0') AS place_origin_return,
                NULLIF(LTRIM(RTRIM(place_destination_return)), '0') AS place_destination_return,
                NULLIF(LTRIM(RTRIM(fk_departure_ota_bus_company)), '0') AS departure_bus_company,
                NULLIF(LTRIM(RTRIM(fk_return_ota_bus_company)), '0') AS return_bus_company,
                CASE 
                    WHEN TRY_CONVERT(DECIMAL(12,2), gmv_success) >= 0 
                         THEN TRY_CONVERT(DECIMAL(12,2), gmv_success)
                    ELSE NULL
                END AS gmv_success,
                TRY_CONVERT(INT, total_tickets_quantity_success) AS total_tickets_qty
            FROM bronze.df_t
        ),
        clean AS (
            SELECT
                b.customer_id,
                b.purchase_datetime,
                b.place_origin_departure,
                b.place_destination_departure,
                b.place_origin_return,
                b.place_destination_return,
                b.departure_bus_company,
                b.return_bus_company,
                b.gmv_success,
                b.total_tickets_qty,
                DATEPART(MONTH, b.purchase_datetime) AS purchase_month,
                DATEPART(ISO_WEEK, b.purchase_datetime) AS purchase_week,
                ((DATEPART(WEEKDAY, b.purchase_datetime) + @@DATEFIRST + 5) % 7) + 1 AS purchase_dayofweek,
                CASE
                    WHEN DATEPART(HOUR, b.purchase_datetime) BETWEEN 6 AND 11 THEN 'morning'
                    WHEN DATEPART(HOUR, b.purchase_datetime) BETWEEN 12 AND 17 THEN 'afternoon'
                    ELSE 'night'
                END AS purchase_period
            FROM base b
            WHERE b.customer_id IS NOT NULL
              AND b.purchase_datetime IS NOT NULL
              AND b.place_destination_departure IS NOT NULL
        )
        INSERT INTO silver.purchases_clean (
            customer_id, purchase_datetime,
            place_origin_departure, place_destination_departure,
            place_origin_return, place_destination_return,
            departure_bus_company, return_bus_company,
            gmv_success, total_tickets_qty,
            purchase_month, purchase_week, purchase_dayofweek, purchase_period
        )
        SELECT
            customer_id, purchase_datetime,
            place_origin_departure, place_destination_departure,
            place_origin_return, place_destination_return,
            departure_bus_company, return_bus_company,
            gmv_success, total_tickets_qty,
            purchase_month, purchase_week, purchase_dayofweek, purchase_period
        FROM clean;

        DECLARE @today DATE = (SELECT CAST(MAX(purchase_datetime) AS DATE) FROM silver.purchases_clean);
        DECLARE @cut30  DATETIME2(0) = DATEADD(DAY, -30,  @today);
        DECLARE @cut90  DATETIME2(0) = DATEADD(DAY, -90,  @today);
        DECLARE @cut180 DATETIME2(0) = DATEADD(DAY, -180, @today);

        ;WITH agg AS (
            SELECT
                c.customer_id,
                MAX(c.purchase_datetime) AS last_purchase,
                SUM(CASE WHEN c.purchase_datetime > @cut30  THEN 1 ELSE 0 END) AS purchases_last_30d,
                SUM(CASE WHEN c.purchase_datetime > @cut90  THEN 1 ELSE 0 END) AS purchases_last_90d,
                SUM(CASE WHEN c.purchase_datetime > @cut180 THEN 1 ELSE 0 END) AS purchases_last_180d,
                COUNT(*) AS total_purchases_lifetime,
                AVG(CAST(c.gmv_success AS DECIMAL(12,2))) AS ticket_medio
            FROM silver.purchases_clean c
            GROUP BY c.customer_id
        ),
        last_order AS (
            SELECT
                c.customer_id,
                c.purchase_datetime,
                c.purchase_month,
                c.purchase_week,
                c.purchase_dayofweek,
                c.purchase_period,
                ROW_NUMBER() OVER (PARTITION BY c.customer_id ORDER BY c.purchase_datetime DESC) AS rn
            FROM silver.purchases_clean c
        ),
        top_dest AS (
            SELECT customer_id, place_destination_departure,
                   ROW_NUMBER() OVER (
                        PARTITION BY customer_id
                        ORDER BY COUNT(*) DESC, MAX(purchase_datetime) DESC
                   ) AS rn
            FROM silver.purchases_clean
            GROUP BY customer_id, place_destination_departure
        )
        INSERT INTO silver.clients_features (
            customer_id, last_purchase, days_since_last_purchase,
            purchases_last_30d, purchases_last_90d, purchases_last_180d, total_purchases_lifetime,
            top_destination,
            last_purchase_month, last_purchase_week, last_purchase_dayofweek, last_purchase_period,
            ticket_medio
        )
        SELECT
            a.customer_id,
            a.last_purchase,
            DATEDIFF(DAY, a.last_purchase, @today) AS days_since_last_purchase,
            a.purchases_last_30d, a.purchases_last_90d, a.purchases_last_180d, a.total_purchases_lifetime,
            td.place_destination_departure AS top_destination,
            lo.purchase_month, lo.purchase_week, lo.purchase_dayofweek, lo.purchase_period,
            a.ticket_medio
        FROM agg a
        JOIN last_order lo
          ON lo.customer_id = a.customer_id AND lo.rn = 1
        LEFT JOIN top_dest td
          ON td.customer_id = a.customer_id AND td.rn = 1;

        PRINT 'Carga do Silver concluída com sucesso.';
    END TRY
    BEGIN CATCH
        PRINT 'Erro na procedure silver.load_silver: ' + ERROR_MESSAGE();
        THROW;
    END CATCH
END;
GO
