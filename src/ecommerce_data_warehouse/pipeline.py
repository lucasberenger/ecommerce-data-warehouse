from ecommerce_data_warehouse.extract import read_csv
from ecommerce_data_warehouse.load import load_dataframe

def execute_pipeline(dataset):
    df = read_csv(dataset["file"])

    load_dataframe(
        df,
        dataset["table"]
    )