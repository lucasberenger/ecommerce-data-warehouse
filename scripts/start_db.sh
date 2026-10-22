#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
    echo "Docker não encontrado." >&2
    exit 1
fi
docker compose version >/dev/null
docker compose up -d db

echo "Aguardando o PostgreSQL..."
ready=false
for ((attempt = 1; attempt <= 30; attempt++)); do
    if docker compose exec -T db sh -c \
        'exec pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 2
done
if [[ "$ready" != true ]]; then
    echo "PostgreSQL indisponível após 30 tentativas. Consulte: docker compose logs db" >&2
    exit 1
fi

psql_in_container() {
    docker compose exec -T db sh -c \
        'exec psql -X --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --set=ON_ERROR_STOP=1 "$@"' \
        sh "$@"
}

# Check only the presence of the expected tables, not their column definitions.
existing_tables="$(psql_in_container --tuples-only --no-align --command="
    SELECT count(*) FROM pg_catalog.pg_tables
    WHERE (schemaname, tablename) IN (
        ('staging', 'customers'),
        ('staging', 'orders'),
        ('staging', 'order_items'),
        ('staging', 'products'),
        ('staging', 'payments'),
        ('analytics', 'dim_customers')
    );")"

case "$existing_tables" in
    6)
        echo "As seis tabelas já existem. DDLs não reaplicados; dados preservados."
        ;;
    0)
        echo "Aplicando os DDLs existentes em uma única transação..."
        psql_in_container --single-transaction \
            --file=/sql/staging/01_create_schemas.sql \
            --file=/sql/staging/02_create_staging.sql \
            --file=/sql/analytics/01_create_schemas.sql \
            --file=/sql/analytics/02_create_analytics.sql
        echo "Tabelas criadas com sucesso."
        ;;
    *)
        echo "Estrutura parcial ou resultado inesperado ($existing_tables). Revise o banco antes de prosseguir." >&2
        exit 1
        ;;
esac

echo "A ingestão não foi executada."
