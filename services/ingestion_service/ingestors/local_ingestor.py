import re
from typing import Iterator, Optional, Tuple
from pathlib import Path
from .base import BaseIngestor
import logging

logger = logging.getLogger(__name__)
class LocalIngestor(BaseIngestor):
    """
    Concrete ingestor for local directories.
    Reads logs from a local filesystem incrementally.
    """

    def __init__(self, base_path: str = "/app/logs"):
        self.base_path = Path(base_path)
        logger.info(f"[LocalIngestor] Initialized with base_path={self.base_path}")

    def latest_file(self, base_path: str, file_glob: str) -> Optional[str]:
        """
        Returns the latest file (by modified time) in base_path matching file_glob.
        """
        logger.debug(f"[LocalIngestor] latest_file called with base_path={base_path}, file_glob={file_glob}")
        directory = Path(base_path)
        logger.info(f"[LocalIngestor] latest_file directory with base_path={base_path}, file_glob={file_glob}, directory={directory}")
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"[LocalIngestor] Directory {base_path} does not exist or is not a dir.")
            return None

        files = list(directory.glob(file_glob))
        logger.info(f"[LocalIngestor] files {files} directory {directory} and file glob {file_glob}")
        if not files:
            logger.warning(f"[LocalIngestor] No files found in {base_path} with pattern {file_glob}")
            return None

        latest = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"[LocalIngestor] Latest file selected: {latest}")
        logger.info(f"[LocalIngestor] latest_file directory2 with base_path={base_path}, file_glob={file_glob}, directory={directory}")
        return str(latest)

    def incremental_read(
        self,
        file_ident: str,
        start_offset: int,
        include_regex: Optional[str],
        exclude_regex: Optional[str],
    ) -> Iterator[Tuple[str, int]]:
        """
        Incrementally read a file from start_offset, yielding (line, new_offset) pairs.
        Filters lines using include/exclude regex if provided.
        """
        
        logger.debug(f"[LocalIngestor] incremental_read called with file={file_ident}, start_offset={start_offset}, "
                     f"include_regex={include_regex}, exclude_regex={exclude_regex}")
        file_path = Path(file_ident)
        if not file_path.exists():
            logger.error(f"[LocalIngestor] File not found: {file_ident}")
            return

        include_pat = re.compile(include_regex) if include_regex else None
        exclude_pat = re.compile(exclude_regex) if exclude_regex else None

        with open(file_path, "r", encoding="utf-8") as f:
            f.seek(start_offset)  # resume from last offset
            logger.info(f"[LocalIngestor] Starting read from offset={start_offset} in file={file_ident}")

            while True:
                line = f.readline()
                if not line:
                    logger.debug("[LocalIngestor] Reached EOF")
                    break  # EOF

                line_stripped = line.rstrip("\n")

                # Apply include/exclude filters
                if include_pat and not include_pat.search(line_stripped):
                    logger.debug(f"[LocalIngestor] Line skipped (no match include_regex): {line_stripped}")
                    continue
                if exclude_pat and exclude_pat.search(line_stripped):
                    logger.debug(f"[LocalIngestor] Line skipped (matched exclude_regex): {line_stripped}")
                    continue

                logger.debug(f"[LocalIngestor] Yielding line='{line_stripped}' at offset={start_offset}")
                yield line_stripped, f.tell()  # get offset safely with readline()
