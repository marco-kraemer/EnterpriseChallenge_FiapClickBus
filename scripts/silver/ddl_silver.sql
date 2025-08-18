USE EnterpriseChallengeClickBus;
GO

IF OBJECT_ID('silver.purchases_clean', 'U') IS NOT NULL
    DROP TABLE silver.purchases_clean;
GO

CREATE TABLE silver.purchases_clean (
    purchase_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_id NVARCHAR(128) NOT NULL,
    purchase_datetime DATETIME2(0) NOT NULL,
    place_origin_departure NVARCHAR(255) NULL,
    place_destination_departure NVARCHAR(255) NULL,
    place_origin_return NVARCHAR(255) NULL,
    place_destination_return NVARCHAR(255) NULL,
    departure_bus_company NVARCHAR(255) NULL,
    return_bus_company NVARCHAR(255) NULL,
    gmv_success DECIMAL(12,2) NULL CHECK (gmv_success >= 0),
    total_tickets_qty INT NULL CHECK (total_tickets_qty >= 0),
    purchase_month TINYINT NOT NULL CHECK (purchase_month BETWEEN 1 AND 12),
    purchase_week TINYINT NOT NULL CHECK (purchase_week BETWEEN 1 AND 53),
    purchase_dayofweek TINYINT NOT NULL CHECK (purchase_dayofweek BETWEEN 1 AND 7),
    purchase_period VARCHAR(16) NOT NULL
);
GO

IF OBJECT_ID('silver.clients_features', 'U') IS NOT NULL
    DROP TABLE silver.clients_features;
GO

CREATE TABLE silver.clients_features (
    customer_id NVARCHAR(128) NOT NULL PRIMARY KEY,
    last_purchase DATETIME2(0) NOT NULL,
    days_since_last_purchase INT NOT NULL,
    purchases_last_30d INT NOT NULL,
    purchases_last_90d INT NOT NULL,
    purchases_last_180d INT NOT NULL,
    total_purchases_lifetime INT NOT NULL,
    top_destination NVARCHAR(255) NULL,
    last_purchase_month TINYINT NULL CHECK (last_purchase_month BETWEEN 1 AND 12),
    last_purchase_week TINYINT NULL CHECK (last_purchase_week BETWEEN 1 AND 53),
    last_purchase_dayofweek TINYINT NULL CHECK (last_purchase_dayofweek BETWEEN 1 AND 7),
    last_purchase_period VARCHAR(16) NULL,
    ticket_medio DECIMAL(12,2) NULL CHECK (ticket_medio >= 0)
);
GO

CREATE INDEX IX_silver_purchases_clean_customer_datetime
    ON silver.purchases_clean (customer_id, purchase_datetime);

CREATE INDEX IX_silver_purchases_clean_dest
    ON silver.purchases_clean (customer_id, place_destination_departure);
