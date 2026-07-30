import pandas as pd
from ecommerce_data_warehouse.database import engine

def load_dataframe(
        df: pd.DataFrame,
        table_name: str,
        schema: str = "staging",
):
    df.to_sql(
        name=table_name,
        con=engine,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    