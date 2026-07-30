from ecommerce_data_warehouse.datasets import DATASETS
from ecommerce_data_warehouse.pipeline import execute_pipeline

def main():
    for name, dataset in DATASETS.items():
        print(f"Processing {name}")

        execute_pipeline(dataset)

    print("Pipeline completed!")


if __name__ == "__main__":
    main()


