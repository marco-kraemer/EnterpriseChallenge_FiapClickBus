use master;
go

IF EXISTS (SELECT 1 FROM sys.databases WHERE name = 'EnterpriseChallengeClickBus')
BEGIN
	ALTER DATABASE EnterpriseChallengeClickBus SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
	DROP DATABASE EnterpriseChallengeClickBus;
END;
GO

create database EnterpriseChallengeClickBus;
go

use EnterpriseChallengeClickBus;
go

create schema bronze;
go
create schema silver;
go
create schema ml;
go
create schema gold;