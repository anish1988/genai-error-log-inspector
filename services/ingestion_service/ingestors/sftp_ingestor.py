import fnmatch, paramiko, re
import logging
from .base import BaseIngestor

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Or INFO in production

# Optional: if not already configured globally, add console handler
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class SFTPIngestor(BaseIngestor):
    def __init__(self, host: str, port: int, username: str, key_path: str):
        self.host, self.port, self.username, self.key_path = host, port, username, key_path
        logger.info(f"SFTPIngestor initialized for host={host}, port={port}, user={username}")

    def _client(self):
        logger.debug(f"Connecting to SFTP {self.host}:{self.port} with key {self.key_path}")
        pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, pkey=pkey)
        logger.info(f"SFTP connection established to {self.host}:{self.port}")
        return paramiko.SFTPClient.from_transport(transport), transport

    def latest_file(self, base_path: str, file_glob: str):
        sftp, transport = self._client()
        logger.debug(f"Fetching latest file from {base_path} matching {file_glob}")
        try:
            entries = sftp.listdir_attr(base_path)
            candidates = [e for e in entries if fnmatch.fnmatch(e.filename, file_glob)]
            logger.debug(f"Found {len(candidates)} matching files")
            if not candidates: 
                logger.warning(f"No matching files found in {base_path} for {file_glob}")
                return None
            latest = max(candidates, key=lambda e: e.st_mtime)
            latest_path = f"{base_path.rstrip('/')}/{latest.filename}"
            logger.info(f"Latest file: {latest_path} (mtime={latest.st_mtime})")
            return latest_path
        finally:
            logger.debug("Closing SFTP connection after latest_file()")
            sftp.close(); transport.close()

    def incremental_read(self, file_ident: str, start_offset: int,
                         include_regex: str | None, exclude_regex: str | None):
        logger.debug(f"Reading file {file_ident} from offset {start_offset}")
        inc = re.compile(include_regex) if include_regex else re.compile(r"(ERROR|EXCEPTION|FATAL|CRITICAL)", re.I)
        exc = re.compile(exclude_regex) if exclude_regex else None

        sftp, transport = self._client()
        try:
            with sftp.open(file_ident, "r") as fh:
                fh.seek(start_offset)
                logger.info(f"Started incremental read on {file_ident} (offset={start_offset})")
                for raw in fh:
                    line = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else raw
                    new_offset = fh.tell()
                    if inc.search(line) and not (exc and exc.search(line)):
                        logger.debug(f"Matched log line at offset={new_offset}: {line.strip()[:120]}")
                        yield line.rstrip("\n"), new_offset
        finally:
            logger.debug("Closing SFTP connection after incremental_read()")
            sftp.close(); transport.close()
