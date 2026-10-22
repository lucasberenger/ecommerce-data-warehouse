import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

def truncate_table(table_name: str, connection: Connection, schema: str = 'staging'):
    # Names come from the internal dataset catalog.
    preparer = connection.dialect.identifier_preparer
    qualified_name = f'{preparer.quote_schema(schema)}.{preparer.quote(table_name)}'
    connection.execute(text(f'TRUNCATE TABLE {qualified_name};'))

def load_dataframe(
        df: pd.DataFrame,
        table_name: str,
        connection: Connection,
        schema: str = "staging",
) -> int:
    if df is None:
        raise ValueError(f'{table_name}: DataFrame is None.')
    if df.empty:
        raise ValueError(f'{table_name}: DataFrame is empty.')

    df.to_sql(
        name=table_name,
        con=connection,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    return len(df)
    