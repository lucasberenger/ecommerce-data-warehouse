import logging

from ecommerce_data_warehouse.datasets import DATASETS
from ecommerce_data_warehouse.pipeline import execute_pipeline
from ecommerce_data_warehouse.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Starting full staging refresh...")
    try:
        results = execute_pipeline(datasets=DATASETS)
    except Exception:
        logger.exception("Staging refresh failed; no new load was confirmed.")
        return 1

    logger.info("Staging refresh committed successfully.")
    logger.info("Execution summary:")
    for result in results:
        logger.info(
            "%-15s %-8s %d rows",
            result.table,
            result.status.value,
            result.rows,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
