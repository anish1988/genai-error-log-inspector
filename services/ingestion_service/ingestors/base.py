from abc import ABC, abstractmethod

class Ingestor(ABC):
    @abstractmethod
    def fetch_latest_log(self, log_types):
        """Fetch the most recent log file for given log types"""
        pass
