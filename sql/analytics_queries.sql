
-- ==========================================
-- RETAIL OMNICHANNEL BUSINESS ANALYTICS
-- ==========================================

-- 1. Overall warehouse summary
SELECT
    COUNT(*) AS total_sales_records,
    SUM(quantity) AS total_quantity,
    ROUND(SUM(total_amount), 2) AS total_recorded_amount
FROM fact_sales;

-- 2. Sales records by source
SELECT
    source_system,
    COUNT(*) AS total_records,
    SUM(quantity) AS total_quantity,
    ROUND(SUM(total_amount), 2) AS recorded_amount
FROM fact_sales
GROUP BY source_system
ORDER BY source_system;

-- 3. Top 10 products by recorded sales amount
SELECT
    p.product_name,
    SUM(f.quantity) AS units_sold,
    ROUND(SUM(f.total_amount), 2) AS recorded_sales
FROM fact_sales f
JOIN dim_product p
    ON f.product_key = p.product_key
GROUP BY p.product_name
ORDER BY recorded_sales DESC
LIMIT 10;

-- 4. Sales by customer source and city
SELECT
    c.source_system,
    c.city,
    COUNT(*) AS sales_records,
    ROUND(SUM(f.total_amount), 2) AS recorded_sales
FROM fact_sales f
JOIN dim_customer c
    ON f.customer_key = c.customer_key
GROUP BY c.source_system, c.city
ORDER BY recorded_sales DESC;

-- 5. Sales by channel
SELECT
    COALESCE(channel, 'Not Available') AS sales_channel,
    COUNT(*) AS total_records,
    ROUND(SUM(total_amount), 2) AS recorded_sales
FROM fact_sales
GROUP BY channel
ORDER BY recorded_sales DESC;

-- 6. Customer history (SCD Type 2)
SELECT
    source_system,
    customer_id,
    customer_name,
    city,
    effective_start_date,
    effective_end_date,
    is_current
FROM dim_customer
WHERE source_system = 'CSV'
  AND customer_id = 'C101'
ORDER BY effective_start_date;

-- 7. Reconciliation against expected source counts
SELECT
    source_system,
    COUNT(*) AS warehouse_records
FROM fact_sales
GROUP BY source_system
ORDER BY source_system;
