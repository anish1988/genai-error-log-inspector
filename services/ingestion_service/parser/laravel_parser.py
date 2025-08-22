import re
from typing import List, Dict
from .base_parser import BaseParser

class LaravelParser(BaseParser):
    def parse(self, file_path: str) -> List[Dict]:
        entries = []
        with open(file_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        current_entry = []
        for line in raw_lines:
            # Laravel log lines often start with a date like [2025-08-17 10:12:34]
            if re.match(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]', line):
                if current_entry:
                    entries.append({"raw": "".join(current_entry).strip()})
                    current_entry = []
            current_entry.append(line)

        if current_entry:
            entries.append({"raw": "".join(current_entry).strip()})
        return entries
