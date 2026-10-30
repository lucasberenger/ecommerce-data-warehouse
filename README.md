# E-commerce Data Warehouse

A portfolio project that brings Olist customer, order, product, item, and payment data together to support consistent business analysis.

The goal is to build a reliable foundation for understanding sales performance, customer purchasing behavior, and delivery outcomes. The project is being developed incrementally, with an emphasis on SQL, dimensional modeling, data quality, and explaining how business metrics are calculated.

## Business purpose

E-commerce decisions require a consistent view of what customers ordered, how they paid, and whether their orders were delivered. These records have different levels of detail: one order can contain several items and several payment records. Combining them without accounting for those differences can overstate sales or payment totals.

This project aims to make those relationships explicit and provide documented, reproducible metrics for commercial and operational analysis.

## Planned business questions

| Area | Questions the warehouse is intended to answer |
|---|---|
| Sales performance | How do order volume, sales value, and average order value change over time? |
| Product mix | Which product categories contribute most to sales? |
| Customers | How does purchasing vary by location, and how often do customers return? |
| Payments | How do payment methods and installment counts vary across orders? |
| Delivery | How often are orders delivered late, and how does this vary by region? |

These are planned analyses, not published findings. Definitions such as eligible order statuses, the treatment of freight, and the date used for monthly reporting still need to be agreed before metrics are implemented.

## Data scope

The repository contains five Olist CSV datasets:

- **Customers:** customer identifiers and location attributes.
- **Orders:** order status and purchase, approval, shipping, and delivery timestamps.
- **Order items:** products, sellers, prices, and freight at order-item level.
- **Products:** categories and descriptive attributes.
- **Payments:** payment methods, values, installment counts, and payment sequence within each order.

The included purchase timestamps span September 2016 to October 2018. This is a historical dataset; the project does not ingest live transactions.

## Current progress

The current implementation provides a staging foundation. It reads the five datasets, applies a small column-name correction, and replaces staging data in a single transaction. SQL checks for missing keys, duplicate keys, and unmatched references are integrated before the load is committed.

The analytical warehouse is still under development. An initial customer dimension definition exists, but dimension loading, fact tables, business metrics, and visualizations have not been implemented.

Next milestones are to validate the quality checks and rollback behavior against PostgreSQL, agree on metric definitions, design the dimensional model, and produce business analyses with documented assumptions.

## Technical guide

### Stack and repository structure

- Python 3.14 or later, with dependencies managed by uv.
- pandas for CSV ingestion and transformations.
- SQLAlchemy and psycopg2 for database access.
- PostgreSQL 16, running locally through Docker Compose.
- SQL for quality rules and database definitions.
- unittest for automated tests.

```text
data/raw/                          Source CSV files
scripts/start_db.sh                 Database startup and initial table creation
sql/staging/                       Staging schema and table definitions
sql/analytics/                     Initial analytical schema definitions
sql/quality/                       Named SQL quality checks
src/ecommerce_data_warehouse/       Python ingestion pipeline
tests/                             Automated tests
```

### Local setup

Prerequisites: Python 3.14+, uv, Bash, Docker, and Docker Compose. Run the following commands from the repository root. Python runs on the host; PostgreSQL runs in a container.

Create the local configuration if you do not already have one:

```sh
cp .env.example .env
```

Review the values before starting the database. `.env` is ignored by Git; the example credentials are for local development.

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | Database address used by Python |
| `POSTGRES_PORT` | `5432` | Host port published by Docker Compose |
| `POSTGRES_DB` | `ecomm_db` | Database name |
| `POSTGRES_USER` | `ecomm_admin` | Database user |
| `POSTGRES_PASSWORD` | `ecomm_passwd` | Database password |

Python and Compose read `.env`; existing environment variables take precedence. Use consistent values in the terminals running each component. PostgreSQL always uses port `5432` inside the container: setting `POSTGRES_PORT=5433` publishes it as `localhost:5433` for Python.

Database name, user, and password initialize a new PostgreSQL volume. Changing them does not update an existing database in the `postgres_data` volume. Check its original configuration if connection settings no longer match.

Start the database and prepare its tables:

```sh
bash scripts/start_db.sh
```

The script waits for readiness for up to 30 attempts, with two-second intervals. If none of the six expected tables exists, it applies the four existing DDL files in one transaction. If all six exist, it skips creation. A partial structure causes it to stop for review. It does not compare column definitions, migrate schemas, remove data, or execute ingestion.

Expected tables are `staging.customers`, `staging.orders`, `staging.order_items`, `staging.products`, `staging.payments`, and `analytics.dim_customers`.

Install the locked dependencies and run ingestion:

```sh
uv sync --locked
uv run ecommerce-data-warehouse
```

A successful run reports `Staging refresh committed successfully.` and a row-count summary. The process exits with `0` on success and `1` on failure.

### Refresh strategy and quality checks

The pipeline performs a full refresh of the five staging tables:

1. Read and validate both SQL check files, including unique check names across files.
2. Read, transform, and validate all five CSVs, rejecting empty datasets.
3. Open one transaction and clear the five staging tables.
4. Insert every dataset using the same connection.
5. Run all 14 SQL checks using that connection.
6. Commit only if every step succeeds.

The checks are defined in [01_check_keys.sql](sql/quality/01_check_keys.sql) and [02_check_references.sql](sql/quality/02_check_references.sql). Each `-- check: name` marker starts one check. A check passes when its query returns no rows; any returned row or SQL execution error prevents the commit. Names, queries, and files must not be empty, and content before the first marker is rejected unless it is whitespace.

Errors before commit roll back the replacement, preserving the previously committed staging data. Repeating a successful load with the same files is intended to produce the same content without duplicates; physical row order is not guaranteed. Analytics tables are outside this refresh.

This approach favors simplicity for static CSVs. It keeps all five DataFrames in memory and holds exclusive table locks during replacement, so concurrent readers may wait. Incremental ingestion is outside the current scope.

### Database inspection and troubleshooting

Open an interactive PostgreSQL session:

```sh
docker compose exec db sh -c 'exec psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Inside `psql`, inspect the tables:

```text
\dt staging.*
\dt analytics.*
\q
```

To run one quality file manually:

```sh
docker compose exec -T db sh -c 'exec psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f /sql/quality/01_check_keys.sql'
```

The repository's `sql/` directory is mounted at `/sql` in the container. Manual SELECT execution displays violations; returned rows do not make `psql` fail. The Python validator supplies that blocking behavior during ingestion.

For startup failures, inspect `docker compose logs db`. The startup script uses `pg_isready` to check availability; availability alone does not confirm credentials, table definitions, or loaded data.

### Tests and validation status

After installing dependencies:

```sh
uv run python -B -m unittest discover -s tests -v
```

Tests cover the SQL check reader and validator, pipeline orchestration, configuration, and the startup script. They use temporary files, mocked Docker and transaction boundaries, and SQLite in memory for selected SQLAlchemy checks. They do not require PostgreSQL and do not prove PostgreSQL-specific behavior.

The project owner has reported successful PostgreSQL ingestion and a second successful execution of the full refresh. The recently integrated quality checks still need an end-to-end PostgreSQL run. Remaining integration validation includes comparing full staging content across repeated loads and deliberately triggering a failure after inserts to verify that all five tables retain their prior contents. The failure scenario should also be tested with initially empty staging tables and checked for unintended analytics changes.

A missing input file tests preparation failure; it does not demonstrate rollback because preparation happens before the transaction starts.
