# services/ingestion_service/ingestors/base.py

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Tuple

class BaseIngestor(ABC):
    """
    Abstract base class for all ingestors.
    Defines the required methods for reading logs incrementally.
    """

    @abstractmethod
    def latest_file(self, base_path: str, file_glob: str) -> Optional[str]:
        """
        Return the path to the latest file matching file_glob in base_path.
        """
        pass

    @abstractmethod
    def incremental_read(
        self,
        file_ident: str,
        start_offset: int,
        include_regex: Optional[str],
        exclude_regex: Optional[str],
    ) -> Iterator[Tuple[str, int]]:
        """
        Yield (line, new_offset) pairs starting from start_offset in file_ident,
        applying include/exclude regex filters.
        """
        pass
