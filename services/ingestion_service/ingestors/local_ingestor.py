import os
from datetime import datetime
from .base import Ingestor

class LocalIngestor(Ingestor):
    def __init__(self, log_path):
        self.log_path = log_path

    def fetch_latest_log(self, log_types):
        files = [
            f for f in os.listdir(self.log_path)
            if any(lt in f for lt in log_types)
        ]
        if not files:
            return None
        latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.log_path, f)))
        with open(os.path.join(self.log_path, latest), 'r') as f:
            return f.read()
