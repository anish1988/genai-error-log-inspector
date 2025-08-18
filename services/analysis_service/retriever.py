class ContextRetriever:
    # In real life, pull from KB, wiki, tickets, vector DB, etc.
    def fetch_context(self, cluster_name: str, log_type: str) -> str:
        return f"Known context for {cluster_name}/{log_type}: (none configured)"
