CREATE OR ALTER PROCEDURE bronze.load_bronze AS
BEGIN
    DECLARE @start_time DATETIME, @end_time DATETIME, @batch_start_time DATETIME, @batch_end_time DATETIME;

    BEGIN TRY
        SET @batch_start_time = GETDATE();
        PRINT '======================================';
        PRINT 'Starting Bronze Load: df_t';
        PRINT '======================================';

        SET @start_time = GETDATE();
        PRINT '>> Truncating Table: bronze.df_t';
        TRUNCATE TABLE bronze.df_t;

        PRINT '>> Inserting Data: bronze.df_t';

        BULK INSERT bronze.df_t
        FROM 'C:\Users\marco\Projetos\Fiap\RoadWise\datasets\df_t.csv'
        WITH (
            FIRSTROW = 2,
            FIELDTERMINATOR = ',',
            ROWTERMINATOR = '0x0a',
            CODEPAGE = '65001',
            TABLOCK
        );

        SET @end_time = GETDATE();
        PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '--------------------------------------';

        PRINT '======================================';
        PRINT 'Bronze Load Completed Successfully';
        SET @batch_end_time = GETDATE();
        PRINT '>> Batch Load Duration: ' + CAST(DATEDIFF(second, @batch_start_time, @batch_end_time) AS NVARCHAR) + ' seconds';
        PRINT '======================================';
    END TRY

    BEGIN CATCH
        PRINT '======================================';
        PRINT 'ERROR during Bronze Load (df_t)';
        PRINT 'Check the message and line number below:';
        PRINT ERROR_MESSAGE();
        PRINT 'Line: ' + CAST(ERROR_LINE() AS VARCHAR);
        PRINT '======================================';
    END CATCH
END;
GO
