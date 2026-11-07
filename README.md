# Retail Omnichannel Sales Data Engineering Capstone

## Project Overview
A multi-source retail data engineering pipeline that ingests, validates, cleans, integrates, and loads retail sales data into a PostgreSQL data warehouse.

## Technologies
- Python
- Pandas
- REST API
- PostgreSQL
- SQLAlchemy
- Requests
- Pytest
- PowerShell

## Architecture
CSV, REST API and PostgreSQL Sources → Bronze Layer → Validation and Cleaning → Silver Layer → Multi-source Integration → PostgreSQL Data Warehouse → SQL Analytics

## Data Sources
- CSV retail orders, customers, and products.
- DummyJSON ecommerce API (synthetic testing data).
- PostgreSQL source tables.

## Pipeline Features
- Multi-source ingestion.
- Data validation and quarantine.
- Duplicate detection and removal.
- Bronze and Silver data layers.
- Unified order dataset.
- PostgreSQL star schema.
- Customer SCD Type 2.
- Fact and dimension loading.
- Idempotent fact loading.
- SQL analytics and reconciliation.

## Warehouse Tables
- dim_customer
- dim_product
- dim_date
- fact_sales

## Validation Results
**Final validation: 8/8 checks passed.**

- Unified records match fact records.
- No duplicate fact business keys.
- No missing customer or product keys.
- One current customer version per customer.
- Source-wise record counts match.
- Customer, product, and date dimensions are populated.

## Installation
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure PostgreSQL credentials in a local `.env` file. Never commit credentials.

## Execution Order
Run from the project root:

```powershell
python src/ingestion/csv_ingestion.py
python src/quality/validate_orders.py
python src/ingestion/api_ingestion.py
python src/quality/validate_api_orders.py
python src/ingestion/postgres_ingestion.py
python src/quality/validate_postgres_orders.py
python src/transformations/unify_orders.py
python src/warehouse/load_dimensions.py
python src/warehouse/load_fact_sales.py
python src/quality/final_validation.py
```

Execute:
- `sql/warehouse_schema.sql`
- `sql/analytics_queries.sql`

## Important Notes
- DummyJSON contains synthetic ecommerce data, not real transactions.
- Some API customer and order attributes are unavailable and are not fabricated.
- Source currencies are unconfirmed. Combined amounts are not verified INR revenue.
- Full CDC and Airflow orchestration are future enhancements.

## Documentation
See `docs/project_report.md` for detailed project documentation.

## End-to-End Pipeline Execution

Run the complete pipeline using:

```powershell
python src\run_pipeline.py

The master script executes all 11 pipeline steps, from source ingestion to Gold layer export.

## Gold Layer Outputs
- data/gold/sales_summary_by_source.csv
- data/gold/sales_summary_by_product.csv
- data/gold/sales_summary_by_city.csv

## Testing
Run:
python -m pytest -v

Result: 7 tests passed.

## Execution Logs
logs/pipeline_run.log

## Final Results
- Unified records: 799
- Fact sales records: 799
- Customer history: 219
- Current customers: 218
- Products: 199
- Date records: 7
- Warehouse validation: 8/8 checks passed
- Automated tests: 7/7 passed

Note: REST API data is synthetic. Source currencies are unconfirmed.