EXPECTED_COLUMNS = {
    "customers": {
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    },
}


def validate_dataframe(df, table):
    expected = EXPECTED_COLUMNS[table]

    missing = expected - set(df.columns)

    if missing:
        raise ValueError(
            f"{table}: missing columns {missing}"
        )