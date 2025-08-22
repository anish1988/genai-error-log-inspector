from typing import List, Dict
from .retriever import ContextRetriever
from .enricher import Enricher
from .llm_client import LLMClient
from services.ingestion_service.parser.laravel_parser import LaravelParser
from services.writer.file_writer import FileWriter
import logging
from datetime import datetime
import os
from pathlib import Path

# Configure logger once (could also be in a separate logging.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

OUTPUT_BASE = os.getenv(
    "OUTPUT_BASE",
    os.path.join(os.getcwd(), "processed_output")  # falls back to ./processed_output
)
OUTPUT_BASE = Path(os.getenv("OUTPUT_BASE", Path.cwd() / "processed_output"))
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)  # ensure base exists

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
        Keep this method for backward compatibility.
        But instead of analyzing raw 'structured' list,
        call analyze_log_file() with the actual file path and log_type.
        """
        logger.info("Starting analysis pipeline")
        logger.info("Cluster=%s | LogType=%s | Source=%s | EventCount=%d",
                    cluster_name, log_type, source_file, len(events))
        
        # Step 1: retrieve context (SRE runbooks, known issues, etc.)
        logger.info("Fetching context for cluster=%s log_type=%s", cluster_name, log_type)
        ctx = self.retriever.fetch_context(cluster_name, log_type)
        file_path = Path(source_file)  # reuse source_file param as path
        out_dir = Path(OUTPUT_BASE) / cluster_name / log_type
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / file_path.name

        logger.info("ctx Display:\n%s", ctx)
        # Step 2: enrich events (normalize fields, add tags)
        logger.info("Enriching %d events", len(events))
        enriched = self.enricher.enrich(events, cluster_name=cluster_name, log_type=log_type)
        logger.info("Enriching  enriched events=%s ", enriched)

         # Now delegate to file-based analyzer
        return self.analyze_log_file(
            file_path=file_path,
            log_type=log_type,
            enriched=enriched,
            output_file=output_file
        )
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
    
    def analyze_log_file(self, file_path: Path, log_type: str, enriched, output_file: Path) -> str:
        """
        Parse log file -> analyze entries one by one -> write results to output file.
        """
        if log_type == "laravel":
            parser = LaravelParser()
        else:
            raise ValueError(f"Unsupported log type: {log_type}")

        writer = FileWriter(str(output_file))

        self.logger.info(f"Parsing log file {file_path} as {log_type}")
        entries = parser.parse(str(file_path))

        results = []
        for idx, entry in enumerate(entries, 1):
            self.logger.info(f"Analyzing entry {idx}/{len(entries)}")
            try:
                response = self.llm.analyze(enriched, entry, context={"log_type": log_type})
                writer.write(entry, response)
                results.append({"entry": entry, "analysis": response})
            except Exception as e:
                self.logger.error(f"Error analyzing entry {idx}: {e}")

        return f"Wrote {len(results)} analyses to {output_file}"

