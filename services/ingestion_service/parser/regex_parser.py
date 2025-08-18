
import re
from typing import Dict
from .base_parser import BaseParser

DEFAULT_PATTERNS = [
    re.compile(r'^(?P<ts>\S+\s+\S+)\s+(?P<level>ERROR|CRITICAL|FATAL|Exception)\s+(?P<msg>.+)$', re.I),
    re.compile(r'(?P<level>ERROR|FATAL|CRITICAL)\s*[:\-]\s*(?P<msg>.+)$', re.I)
]

class RegexParser(BaseParser):
    def __init__(self, patterns=None):
        self.patterns = patterns or DEFAULT_PATTERNS

    def parse(self, raw_line: str) -> Dict:
        for pat in self.patterns:
            m = pat.search(raw_line)
            if m:
                d = m.groupdict()
                d["raw"] = raw_line
                return d
        return {"raw": raw_line, "msg": raw_line, "level": "ERROR"}
