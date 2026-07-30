from ecommerce_data_warehouse.datasets import DATASETS
from ecommerce_data_warehouse.pipeline import execute_pipeline
from ecommerce_data_warehouse.logging_config import configure_logging
from ecommerce_data_warehouse.types import PipelineRespose
import logging

configure_logging()

logger = logging.getLogger(__name__)

def main():
    logger.info("Starting ingestion pipeline...\n")

    results = []
    for dataset in DATASETS.values():
        table = dataset['table']
        try:
            rows = execute_pipeline(dataset=dataset)
            logger.info(
                "%s loaded successfully (%d rows)",
                table,
                rows,
            )
            results.append(
                PipelineRespose(
                    table=table,
                    status='SUCCESS',
                    rows=rows,
                )
            )
        except Exception:
            logger.exception(
                "Failed to load %s",
                table,
            )
            results.append(
                PipelineRespose(
                    table=table,
                    status='FAILED',
                    rows=rows,
                )
            )

    logger.info("\nPipeline finished successfully.")
    logger.info('Execution summary:')
    for r in results:
        logger.info(
            "'%-15s %-8s %d rows",
            r['table'],
            r['status'],
            r['rows'],
        )

if __name__ == "__main__":
    main()


