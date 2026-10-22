from ecommerce_data_warehouse.datasets import DATASETS
from ecommerce_data_warehouse.pipeline import execute_pipeline
from ecommerce_data_warehouse.logging_config import configure_logging
from ecommerce_data_warehouse.types import PipelineResponse, PipelineStatus
import logging

configure_logging()

logger = logging.getLogger(__name__)

def main() -> int:
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
                PipelineResponse(
                    table=table,
                    status=PipelineStatus.SUCCESS,
                    rows=rows,
                )
            )
        except Exception:
            logger.exception(
                "Failed to load %s",
                table,
            )
            results.append(
                PipelineResponse(
                    table=table,
                    status=PipelineStatus.FAILED,
                    rows=0,
                )
            )
    failed = any(
        r.status == PipelineStatus.FAILED
        for r in results
    )
    if failed:
        logger.warning('Pipeline finished with failures.')
    else:
        logger.info('Pipeline finished successfully.')
    logger.info('Execution summary:')
    for r in results:
        logger.info(
            "%-15s %-8s %d rows",
            r.table,
            r.status.value,
            r.rows,
        )

    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())


