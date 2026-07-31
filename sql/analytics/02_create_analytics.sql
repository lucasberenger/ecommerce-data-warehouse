CREATE TABLE analytics.dim_customers (
    customer_sk SERIAL PRIMARY KEY,
    customer_unique_id TEXT,
    zip_code_prefix TEXT,
    city_name TEXT,
    state_name CHAR(2),
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);