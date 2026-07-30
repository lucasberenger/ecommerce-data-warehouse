import pandas as pd
from ecommerce_data_warehouse.database import engine
from sqlalchemy import text

def truncate_table(table_name, schema='staging'):
    with engine.begin() as conn:
        conn.execute(
            text(f'TRUNCATE TABLE {schema}.{table_name};')
        )
        
def load_dataframe(
        df: pd.DataFrame,
        table_name: str,
        schema: str = "staging",
) -> int:
    if df is None:
        raise ValueError(f'{table_name}: DataFrame is None.')
    if df.empty:
        raise ValueError(f'{table_name}: DataFrame is empty.')

    df.to_sql(
        name=table_name,
        con=engine,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    return len(df)
    