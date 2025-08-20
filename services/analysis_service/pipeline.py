from typing import List, Dict
from .retriever import ContextRetriever
from .enricher import Enricher
from .llm_client import LLMClient
import logging
from datetime import datetime

# Configure logger once (could also be in a separate logging.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AnalyzerPipeline:
    def __init__(self, retriever: ContextRetriever | None = None,
                 enricher: Enricher | None = None,
                 llm: LLMClient | None = None):
        self.retriever = retriever or ContextRetriever()
        self.enricher = enricher or Enricher()
        self.llm = llm or LLMClient()

    def run(self, events: List[Dict], cluster_name: str, log_type: str, source_file: str) -> str:
        """
        events = [{ts?, level, msg, raw}, ...]
        returns string (persisted as-is to output file)
        """
        logger.info("Starting analysis pipeline")
        logger.info("Cluster=%s | LogType=%s | Source=%s | EventCount=%d",
                    cluster_name, log_type, source_file, len(events))
        
        # Step 1: retrieve context (SRE runbooks, known issues, etc.)
        logger.info("Fetching context for cluster=%s log_type=%s", cluster_name, log_type)
        ctx = self.retriever.fetch_context(cluster_name, log_type)
        logger.info("ctx Display:\n%s", ctx)
        # Step 2: enrich events (normalize fields, add tags)
        logger.info("Enriching %d events", len(events))
        enriched = self.enricher.enrich(events, cluster_name=cluster_name, log_type=log_type)
        logger.info("Enriching  enriched events=%s ", enriched)

        # Step 3: LLM analysis (root cause, fixes, severity)
        logger.info("Sending enriched events to LLM for analysis")
        analysis = self.llm.analyze(enriched, context=ctx)

        # Step 4: format result (simple, human-readable; you can output JSON if you prefer)
        exec_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            f"Execution-Time: {exec_time}",
            f"Cluster: {cluster_name}",
            f"Log-Type: {log_type}",
            f"Source-File: {source_file}",
            f"Log-Entries: {len(events)}",
            "----- Analysis -----",
            analysis,
            "--------------------",
        ]
        result = "\n".join(lines)

        logger.info("Pipeline finished successfully")
        return result
