from typing import List, Dict
from .retriever import ContextRetriever
from .enricher import Enricher
from .llm_client import LLMClient

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
        # Step 1: retrieve context (SRE runbooks, known issues, etc.)
        ctx = self.retriever.fetch_context(cluster_name, log_type)

        # Step 2: enrich events (normalize fields, add tags)
        enriched = self.enricher.enrich(events, cluster_name=cluster_name, log_type=log_type)

        # Step 3: LLM analysis (root cause, fixes, severity)
        analysis = self.llm.analyze(enriched, context=ctx)

        # Step 4: format result (simple, human-readable; you can output JSON if you prefer)
        lines = [
            f"Cluster: {cluster_name}",
            f"Log-Type: {log_type}",
            f"Source-File: {source_file}",
            "----- Analysis -----",
            analysis,
            "--------------------",
        ]
        return "\n".join(lines)
