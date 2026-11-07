
# Retail Omnichannel Sales Data Engineering Capstone

## 1. Project Overview

This project implements a multi-source retail data ingestion and
warehouse pipeline using Python, PostgreSQL and pandas.

The pipeline integrates:
- CSV files
- REST API (DummyJSON synthetic ecommerce data)
- PostgreSQL source tables

The objective is to validate, clean, deduplicate, integrate and
load retail sales data into a dimensional data warehouse.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Pipeline implementation |
| pandas | Data extraction and transformation |
| requests | REST API ingestion |
| PostgreSQL 18 | Source database and warehouse |
| SQLAlchemy | Python-PostgreSQL connection |
| psycopg2 | PostgreSQL driver |
| pytest | Testing framework |
| VS Code | Development environment |

## 3. Architecture

CSV Sources ───────┐
REST API ──────────┼──> Bronze Layer
PostgreSQL ────────┘
                         |
                         v
                  Silver Layer
             Validation and Cleaning
                         |
                         v
                 Unified Dataset
                         |
                         v
                   Gold Layer
             PostgreSQL Data Warehouse
                         |
                         v
                Business Analytics

## 4. Source-to-Target Mapping

| Source | Source Data | Target |
|---|---|---|
| CSV | orders.csv | Bronze orders |
| CSV | customers.csv | Bronze customers |
| CSV | products.csv | Bronze products |
| REST API | DummyJSON carts | Bronze API retail orders |
| PostgreSQL | source_orders | Bronze PostgreSQL orders |
| PostgreSQL | source_customers | Bronze PostgreSQL customers |
| PostgreSQL | source_products | Bronze PostgreSQL products |
| Unified Silver | Customer information | dim_customer |
| Unified Silver | Product information | dim_product |
| Unified Silver | Order dates | dim_date |
| Unified Silver | Sales transactions | fact_sales |

## 5. Data Quality Report

### CSV source

| Metric | Records |
|---|---:|
| Input records | 9 |
| Invalid records | 2 |
| Valid before deduplication | 7 |
| Final clean records | 6 |

Rejections:
- Order 7005: Missing customer ID and unknown customer.
- Order 7006: Invalid negative quantity and amount.

Duplicate order 7003 was resolved by retaining its latest update.

### REST API source

| Metric | Records |
|---|---:|
| Cart records received | 208 |
| Order-item records received | 800 |
| Invalid/duplicate records | 12 |
| Final clean records | 788 |

Validation included required fields, numeric values, amount
consistency and duplicate order-item detection.

### PostgreSQL source

| Metric | Records |
|---|---:|
| Orders received | 5 |
| Invalid records | 0 |
| Final clean records | 5 |

## 6. Multi-Source Reconciliation

| Source | Unified records | Warehouse records |
|---|---:|---:|
| CSV | 6 | 6 |
| REST API | 788 | 788 |
| PostgreSQL | 5 | 5 |
| **Total** | **799** | **799** |

All source counts reconcile.

## 7. Data Warehouse Design

The Gold warehouse contains four tables.

### dim_customer
- Customer surrogate key
- Source system and customer ID
- Customer name, email and city
- Effective start and end dates
- Current-version indicator

SCD Type 2 preserves customer history.

Example:
- Previous city: Hyderabad
- New city: Secunderabad
- Previous record marked not current
- New record marked current

### dim_product
Stores product identifiers, names, categories, brands and prices.

### dim_date
Stores calendar attributes such as day, month, quarter and year.

### fact_sales
Stores sales transactions, quantities, prices, amounts and
foreign keys to the dimensions.

The business key is:
source_system + order_id + product_id.

This prevents collisions across sources and preserves multiple
products within an API cart.

## 8. Reliability Features

Implemented:
- Required-column validation
- Missing-value checks
- Numeric validation
- Sales amount validation
- Customer and product reference validation
- Duplicate detection
- Quarantine of rejected records
- SCD Type 2 customer history
- Duplicate-safe fact loading
- SQLAlchemy transaction handling
- Final warehouse validation
- Reconciliation by source

The fact-loading process was executed twice.
The second execution inserted zero new fact records.

## 9. Final Validation Results

| Validation | Result |
|---|---|
| Unified and fact counts match | PASS |
| No duplicate fact business keys | PASS |
| No missing customer/product keys | PASS |
| One current version per customer | PASS |
| Source-wise reconciliation | PASS |
| Customer dimension populated | PASS |
| Product dimension populated | PASS |
| Date dimension populated | PASS |

Final result: 8/8 checks passed.

## 10. Business Analytics

SQL reports were created for:
- Overall sales and quantity
- Sales by source system
- Top products by recorded amount
- Sales by customer city
- Sales by channel
- Customer history
- Source reconciliation

Warehouse results:
- Fact records: 799
- Total quantity: 2,393
- Combined recorded amount: 3,916,429.04

## 11. Pipeline Execution Log

| Step | Result |
|---|---|
| CSV ingestion | 9 orders, 7 customers, 6 products |
| CSV validation | 6 clean, 2 rejected |
| REST API ingestion | 208 carts, 800 order items |
| REST API validation | 788 clean, 12 rejected |
| PostgreSQL ingestion | 4 customers, 4 products, 5 orders |
| PostgreSQL validation | 5 clean orders |
| Multi-source integration | 799 records |
| Dimension loading | 219 customer history records, 199 products |
| Fact loading | 799 records inserted |
| Idempotency test | 0 additional fact records |
| Final validation | 8/8 passed |

## 12. Known Limitations and Future Improvements

- DummyJSON provides synthetic ecommerce data, not real retailer
  transactions.
- API data does not provide the customer names, cities, order dates
  or sales channels required by every analytical report.
- Source price currencies are not confirmed to be identical.
  Therefore, the combined amount is a numeric total, not verified
  consolidated INR revenue.
- The current fact loader uses duplicate-safe inserts. A full
  change-data-capture process for updating previously loaded sales
  records is a future improvement.
- Automated watermark-based late-arriving record processing can
  be added in a later version.
- Airflow scheduling and monitoring are future improvements.

## 13. Conclusion

The project demonstrates a working beginner-level retail
omnichannel data engineering pipeline.

It integrates multiple sources, validates and cleans records,
creates a unified Silver dataset, loads a PostgreSQL dimensional
warehouse, preserves customer history using SCD Type 2 and
supports business analytics through SQL.

The final warehouse passed all eight automated validation checks.

## Final End-to-End Execution Results

The complete pipeline was executed successfully using:

`python src/run_pipeline.py`

All 11 pipeline stages completed successfully.

### Final Dataset Counts

| Metric | Records |
|---|---:|
| Unified orders | 799 |
| Fact sales | 799 |
| Customer history | 219 |
| Current customers | 218 |
| Products | 199 |
| Date dimension | 7 |

### Automated Testing

- Total tests: 7
- Passed: 7
- Failed: 0

### Warehouse Validation

All 8 final warehouse validation checks passed.

### Gold Layer Exports

Three analytical CSV files were generated:

- `sales_summary_by_source.csv`
- `sales_summary_by_product.csv`
- `sales_summary_by_city.csv`

### Pipeline Execution Logging

The master pipeline runner records execution details in:

`logs/pipeline_run.log`

**Final execution status: SUCCESS.**