import logging

from ecommerce_data_warehouse.database import engine
from ecommerce_data_warehouse.extract import read_csv
from ecommerce_data_warehouse.load import load_dataframe, truncate_table
from ecommerce_data_warehouse.transform import transform_dataframe
from ecommerce_data_warehouse.types import PipelineResponse, PipelineStatus
from ecommerce_data_warehouse.validation import validate_dataframe

logger = logging.getLogger(__name__)


def execute_pipeline(datasets: dict) -> list[PipelineResponse]:
    """Prepare every input, then replace staging in one transaction."""
    prepared = []
    for dataset in datasets.values():
        table = dataset['table']
        logger.info("Preparing %s", table)
        df = read_csv(filename=dataset['file'])
        df = transform_dataframe(df=df, table=table)
        validate_dataframe(df=df, table=table)
        if df.empty:
            raise ValueError(f'{table}: DataFrame is empty.')
        prepared.append((table, df))

    results = []
    with engine.begin() as connection:
        for table, _ in prepared:
            truncate_table(table_name=table, connection=connection)
        for table, df in prepared:
            logger.info("Inserting %s (commit pending)", table)
            rows = load_dataframe(df=df, table_name=table, connection=connection)
            results.append(PipelineResponse(table, PipelineStatus.SUCCESS, rows))

    # The context manager has committed before any success is returned.
    return results
