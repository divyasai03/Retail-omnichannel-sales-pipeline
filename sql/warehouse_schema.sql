
-- ==========================================
-- RETAIL DATA WAREHOUSE: DIMENSION TABLES
-- ==========================================

-- 1. Customer Dimension
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key SERIAL PRIMARY KEY,
    source_system VARCHAR(30) NOT NULL,
    customer_id VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    email VARCHAR(150),
    city VARCHAR(100),
    effective_start_date TIMESTAMP NOT NULL,
    effective_end_date TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE
);

-- 2. Product Dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_key SERIAL PRIMARY KEY,
    source_system VARCHAR(30) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    product_name VARCHAR(100),
    category VARCHAR(100),
    brand VARCHAR(100),
    unit_price NUMERIC(12,2)
);

-- 3. Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    day_number INTEGER,
    month_number INTEGER,
    month_name VARCHAR(20),
    quarter_number INTEGER,
    year_number INTEGER,
    day_name VARCHAR(20)
);


-- ==========================================
-- 4. SALES FACT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,

    source_system VARCHAR(30) NOT NULL,
    order_id VARCHAR(30) NOT NULL,
    product_id VARCHAR(30) NOT NULL,

    customer_key INTEGER REFERENCES dim_customer(customer_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    date_key INTEGER REFERENCES dim_date(date_key),

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2),
    total_amount NUMERIC(14,2),

    channel VARCHAR(50),
    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_source_order_product
        UNIQUE (source_system, order_id, product_id)
);
