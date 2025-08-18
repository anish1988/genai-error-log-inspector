import fnmatch, paramiko, re
from .base import BaseIngestor

class SFTPIngestor(BaseIngestor):
    def __init__(self, host: str, port: int, username: str, key_path: str):
        self.host, self.port, self.username, self.key_path = host, port, username, key_path

    def _client(self):
        pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, pkey=pkey)
        return paramiko.SFTPClient.from_transport(transport), transport

    def latest_file(self, base_path: str, file_glob: str):
        sftp, transport = self._client()
        try:
            entries = sftp.listdir_attr(base_path)
            candidates = [e for e in entries if fnmatch.fnmatch(e.filename, file_glob)]
            if not candidates: return None
            latest = max(candidates, key=lambda e: e.st_mtime)
            return f"{base_path.rstrip('/')}/{latest.filename}"
        finally:
            sftp.close(); transport.close()

    def incremental_read(self, file_ident: str, start_offset: int,
                         include_regex: str | None, exclude_regex: str | None):
        inc = re.compile(include_regex) if include_regex else re.compile(r"(ERROR|EXCEPTION|FATAL|CRITICAL)", re.I)
        exc = re.compile(exclude_regex) if exclude_regex else None

        sftp, transport = self._client()
        try:
            with sftp.open(file_ident, "r") as fh:
                fh.seek(start_offset)
                for raw in fh:
                    line = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else raw
                    new_offset = fh.tell()
                    if inc.search(line) and not (exc and exc.search(line)):
                        yield line.rstrip("\n"), new_offset
        finally:
            sftp.close(); transport.close()
