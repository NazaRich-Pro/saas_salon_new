#!/bin/bash
set -e

# PostgreSQL initialization script
# This runs on first container start

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    
    -- Set timezone
    SET timezone = 'UTC';
    
    -- Grant necessary permissions
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- Log initialization
    SELECT 'BeautyHub database initialized successfully' AS status;
EOSQL

echo "PostgreSQL initialization complete"

