from pandas import DataFrame


COLUMN_MAPPINGS = {
    "products": {
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    }
}


def transform_dataframe(df: DataFrame, table: str) -> DataFrame:
    mapping = COLUMN_MAPPINGS.get(table, {})

    return df.rename(columns=mapping)