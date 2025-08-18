
import os
import json
import time
import logging
from datetime import datetime
from typing import List
from pathlib import Path
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from .cluster_manager import ClusterManager
#import ClusterManager from services.ingestion_service.cluster_manager 
from .state_manager import StateManager
from .scheduler import Scheduler
from .parser.regex_parser import RegexParser
from ..analysis_service.pipeline import AnalyzerPipeline
from ..notifications.notifier import Notifier

load_dotenv()

CONFIG_PATH = "config/clusters.yaml"
#OUTPUT_BASE = os.getenv("OUTPUT_BASE", "/app/processed_output")
OUTPUT_BASE = os.getenv(
    "OUTPUT_BASE",
    os.path.join(os.getcwd(), "processed_output")  # falls back to ./processed_output
)
OUTPUT_BASE = Path(os.getenv("OUTPUT_BASE", Path.cwd() / "processed_output"))
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)  # ensure base exists
# ----------------------------------------------------------------------------
# Setup Logging start
# ----------------------------------------------------------------------------
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "execution.log"

logger = logging.getLogger("ExecutionLogger")
logger.setLevel(logging.INFO)


# Rotating log handler: 5MB per file, keep 5 backups
handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# ----------------------------------------------------------------------------
# Setup Logging End
# ----------------------------------------------------------------------------
DB_CFG = {
    "host": os.getenv("DB_HOST", "host.docker.internal"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root@123Abc"),
    "database": os.getenv("DB_NAME", "asterisk"),
}

# ----------------------------------------------------------------------------
# Job Creation
# ----------------------------------------------------------------------------
def make_job():
    cm = ClusterManager(CONFIG_PATH)
    print("DB_CFG CONFIG:", DB_CFG)
    logger.info("ClusterManager initialized with config: %s", CONFIG_PATH)
    logger.info("Database Config: %s", DB_CFG)
    sm = StateManager(DB_CFG)
    parser = RegexParser()
    analyzer = AnalyzerPipeline()     # DI: can swap implementations
    notifier = Notifier()

    def process_unit(cluster, lt):
        print(f"Processing cluster Error writing execution log111: {cluster.name}")
        logger.info("Processing cluster=%s, cluster type=%s, log_type=%s", cluster.name, cluster, lt.name)
        ingestor = cm.ingestor_for(cluster)
        print(f"Ingestor Initialization : {ingestor}")
        # Acceptance Criterion (3): pick most recent file only
        logger.info("Latest file calling before cluster=%s, path=%s, FileGlob=%s", cluster.name, lt.path, lt.file_glob)
        latest = ingestor.latest_file(lt.path, lt.file_glob)
        print(f"latest file checkig: {latest}")
        if not latest:
            print(f"No log file found for cluster, log_type : {cluster.name} ")
            logger.warning("No log file found for cluster=%s, log_type=%s", cluster.name, lt.name)
            return

        print(f"you are here for some reason: {cluster.name}")
        file_ident = str(latest)
        # Derive a stable file key (same as input filename)
        file_key = Path(file_ident).name
        start_offset = sm.get_offset(cluster.name, lt.name, file_key)

        last_offset = start_offset
        new_lines_found = 0
        structured = []

        try:
            for raw, new_offset in ingestor.incremental_read(
                file_ident, start_offset, lt.include_regex, lt.exclude_regex
            ):
                new_lines_found += 1
                structured.append(parser.parse(raw))
                last_offset = new_offset

            if new_lines_found:
                logger.info("Parsed %d new lines from %s", new_lines_found, file_key)
                result_text = analyzer.run(structured, cluster_name=cluster.name, log_type=lt.name, source_file=file_key)
                # Save output to different folder with SAME filename
                out_dir = Path(OUTPUT_BASE) / cluster.name / lt.name
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / file_key                    # same file name
                out_path.write_text(result_text, encoding="utf-8")
                logger.info("Analysis result written to %s", out_path)

            sm.upsert_offset(cluster.name, lt.name, file_key, last_offset)
            logger.info("Updated offset for cluster=%s, log_type=%s, file=%s", cluster.name, lt.name, file_key)


        except Exception as e:
            logger.error(
                "Error processing cluster=%s, log_type=%s, file=%s: %s",
                cluster.name, lt.name, file_key, str(e),
                exc_info=True
            )
            notifier.notify(f"[INGEST ERROR] {cluster.name}/{lt.name} {file_key}: {e}")
            raise

    def run_all():
        logger.info("Starting run_all()")
        units = []
        for c in cm.enabled_clusters():
            for lt in c.log_types:
                logger.info("Enable Clusters form config.yml file cluster=%s ",c)
                logger.info("All log type in  Clusters form config.yml file log types=%s ",lt)
                units.append(lambda c=c, lt=lt: process_unit(c, lt))
        Scheduler(cm.app_cfg.schedule.every_minutes, cm.app_cfg.schedule.parallel).run_batch(units)
        logger.info("Completed run_all() cycle")

    return run_all
# ----------------------------------------------------------------------------
# Main entry
# ----------------------------------------------------------------------------
def main():
    logger.info("Starting ingestion service...")
    job = make_job()
    # schedule loop:
    scheduler = Scheduler(
        every_minutes=int(os.getenv("SCHEDULE_EVERY_MINUTES", "5")),
        parallel=os.getenv("PARALLEL", "true").lower() == "true"
    )
    logger.info(
        "Scheduler started with every_minutes=%s, parallel=%s",
        scheduler.every_minutes, scheduler.parallel
    )
    scheduler.run_forever(job)

if __name__ == "__main__":
    main()
