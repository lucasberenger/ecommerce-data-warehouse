from ecommerce_data_warehouse.extract import read_csv
from ecommerce_data_warehouse.load import load_dataframe
from ecommerce_data_warehouse.transform import transform_dataframe
from ecommerce_data_warehouse.validation import validate_dataframe
import logging

logger = logging.getLogger(__name__)

def execute_pipeline(dataset: dict) -> int:
    table = dataset['table']
    filename = dataset['file']

    df = read_csv(filename=filename)
    df = transform_dataframe(df=df, table=table)
    validate_dataframe(df=df, table=table)

    return load_dataframe(df=df, table_name=table)
