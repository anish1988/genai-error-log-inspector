# Handles connection to multiple log sources (clusters), e.g., SFTP or local dirs.
# SRP: configuration loading + ingestor factory + path resolution.
# OCP: new cluster/ingestor types can be added without changing consumers.
# DIP: high-level orchestration depends on this abstraction, not concrete ingestors.

from __future__ import annotations
import os
from typing import Iterable, Tuple
import yaml

from services.ingestion_service.config import AppConfig, Cluster, LogType
from .ingestors.local_ingestor import LocalIngestor
from .ingestors.sftp_ingestor import SFTPIngestor

class ClusterManager:
    """
    ClusterManager is responsible for:
      - Loading and validating cluster configuration (clusters.yaml -> AppConfig)
      - Selecting enabled clusters
      - Producing the correct Ingestor implementation for a cluster
      - Resolving base paths per (cluster, log_type) with env-aware behavior

    It does NOT perform IO itself (keeps SRP).
    """

    def __init__(self, config_path: str,
                 *,
                 env: str | None = None,
                 local_mount: str | None = None):
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        self.app_cfg = AppConfig(**raw)
        self.env = (env or os.getenv("ENVIRONMENT", "production")).lower()
        # Where host logs are mounted inside the container (compose volume)
        self.local_mount = local_mount or os.getenv("LOCAL_MOUNT_PATH", "/app/logs")

    # ---------- Selection ----------

    def enabled_clusters(self) -> list[Cluster]:
        return [c for c in self.app_cfg.clusters if c.enabled]

    # ---------- Factory ----------

    def ingestor_for(self, cluster: Cluster):
        """
        Returns the appropriate ingestor instance for the given cluster.
        """
        if cluster.type == "local":
            return LocalIngestor()

        if cluster.type == "sftp":
            if not (cluster.host and cluster.username and cluster.key_path):
                raise ValueError(f"SFTP credentials missing for cluster: {cluster.name}")
            return SFTPIngestor(
                host=cluster.host,
                port=cluster.port or 22,
                username=cluster.username,
                key_path=cluster.key_path,
            )

        # Future: add http/syslog implementations here
        raise ValueError(f"Unsupported cluster type: {cluster.type}")

    # ---------- Path resolution ----------

    def resolve_path(self, cluster: Cluster, lt: LogType) -> str:
        """
        Determines the effective base path for this (cluster, log_type).

        - If lt.path is absolute, use it as-is.
        - If lt.path is relative and cluster.type == local:
            join with LOCAL_MOUNT_PATH (the volume mount inside the container).
        - If cluster.type == sftp:
            lt.path should already be an absolute path on the remote host.
        """
        p = lt.path
        if os.path.isabs(p):
            return p

        if cluster.type == "local":
            # Treat relative paths as relative to the mounted host logs directory
            return os.path.join(self.local_mount, p)

        # For SFTP, prefer absolute remote paths in config.
        return p

    # ---------- Work units ----------

    def units(self) -> Iterable[Tuple[Cluster, LogType, str]]:
        """
        Yields (cluster, log_type, resolved_base_path) for every enabled log type.
        Orchestrators can use this to drive ingestion without worrying about path logic.
        """
        for c in self.enabled_clusters():
            for lt in c.log_types:
                yield c, lt, self.resolve_path(c, lt)
