import re
from .base_parser import BaseParser

class RegexParser(BaseParser):
    ERROR_PATTERN = re.compile(r"\[(?P<timestamp>.*?)\]\s+(?P<level>ERROR|EXCEPTION)\s+(?P<message>.+)")

    def parse(self, log_content):
        results = []
        for match in self.ERROR_PATTERN.finditer(log_content):
            results.append({
                "timestamp": match.group("timestamp"),
                "level": match.group("level"),
                "message": match.group("message"),
            })
        return results
