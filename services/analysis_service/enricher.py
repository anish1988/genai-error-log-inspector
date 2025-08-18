from typing import List, Dict

class Enricher:
    def enrich(self, events: List[Dict], cluster_name: str, log_type: str) -> List[Dict]:
        # Normalize and tag
        for e in events:
            e.setdefault("cluster", cluster_name)
            e.setdefault("type", log_type)
        return events
