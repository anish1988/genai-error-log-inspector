from abc import ABC, abstractmethod
from typing import Dict

class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_line: str) -> Dict:
        ...
