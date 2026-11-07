
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline_run.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)

logger = logging.getLogger(__name__)

PIPELINE_STEPS = [
    ("CSV ingestion", "src/ingestion/csv_ingestion.py"),
    ("CSV validation", "src/quality/validate_orders.py"),
    ("REST API ingestion", "src/ingestion/api_ingestion.py"),
    ("REST API validation", "src/quality/validate_api_orders.py"),
    ("PostgreSQL ingestion", "src/ingestion/postgres_ingestion.py"),
    ("PostgreSQL validation", "src/quality/validate_postgres_orders.py"),
    ("Multi-source integration", "src/transformations/unify_orders.py"),
    ("Dimension loading", "src/warehouse/load_dimensions.py"),
    ("Fact table loading", "src/warehouse/load_fact_sales.py"),
    ("Final validation", "src/quality/final_validation.py"),
    ("Gold layer export", "src/warehouse/export_gold.py"),
]


def run_pipeline():
    logger.info("=" * 65)
    logger.info("RETAIL OMNICHANNEL DATA PIPELINE STARTED")
    logger.info("Start time: %s", datetime.now().isoformat())
    logger.info("=" * 65)

    try:
        for number, (step_name, script_path) in enumerate(
            PIPELINE_STEPS, start=1
        ):
            logger.info("STEP %s/%s: %s", number, len(PIPELINE_STEPS), step_name)

            script = BASE_DIR / script_path

            if not script.exists():
                raise FileNotFoundError(
                    f"Pipeline script not found: {script_path}"
                )

            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                logger.info("%s", result.stdout.rstrip())

            if result.stderr:
                logger.warning("%s", result.stderr.rstrip())

            if result.returncode != 0:
                logger.error("FAILED: %s", step_name)
                raise RuntimeError(
                    f"Pipeline stopped because {step_name} failed."
                )

            logger.info("SUCCESS: %s", step_name)

        logger.info("=" * 65)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("End time: %s", datetime.now().isoformat())
        logger.info("=" * 65)

    except Exception:
        logger.exception("PIPELINE EXECUTION FAILED")
        raise


if __name__ == "__main__":
    run_pipeline()
