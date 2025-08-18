IF OBJECT_ID('bronze.df_t', 'U') IS NOT NULL
    DROP TABLE bronze.df_t;
GO

CREATE TABLE bronze.df_t (
    nk_ota_localizer_id            NVARCHAR(MAX) NULL, -- hash id da compra
    fk_contact                     NVARCHAR(MAX) NULL, -- hash id do contato
    date_purchase                  NVARCHAR(MAX) NULL, -- data (yyyy-MM-dd)
    time_purchase                  NVARCHAR(MAX) NULL, -- hora (HH:mm:ss)
    place_origin_departure         NVARCHAR(MAX) NULL, -- hash origem da ida
    place_destination_departure    NVARCHAR(MAX) NULL, -- hash destino da ida
    place_origin_return            NVARCHAR(MAX) NULL, -- hash origem do retorno (0 = sem retorno)
    place_destination_return       NVARCHAR(MAX) NULL, -- hash destino do retorno (0 = sem retorno)
    fk_departure_ota_bus_company   NVARCHAR(MAX) NULL, -- cia de ônibus ida
    fk_return_ota_bus_company      NVARCHAR(MAX) NULL, -- cia de ônibus retorno (1 = sem retorno)
    gmv_success                    NVARCHAR(MAX) NULL, -- valor monetário (ex: 89.09)
    total_tickets_quantity_success NVARCHAR(MAX) NULL  -- quantidade de passagens (ex: 1)
);
GO
