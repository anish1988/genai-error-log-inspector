from pydantic import BaseModel, Field
from typing import Optional, List

class LogType(BaseModel):
    name: str
    path: str
    file_glob: str = Field(default="*.log")
    include_regex: Optional[str] = None
    exclude_regex: Optional[str] = None
    parser: str = "regex_parser"

class Cluster(BaseModel):
    name: str
    enabled: bool = True
    type: str = Field(pattern="^(local|sftp|http|syslog)$")
    host: Optional[str] = None
    port: Optional[int] = 22
    username: Optional[str] = None
    key_path: Optional[str] = None
    log_types: List[LogType]

class ScheduleCfg(BaseModel):
    every_minutes: int = 5
    parallel: bool = True

class AppConfig(BaseModel):
    schedule: ScheduleCfg
    clusters: List[Cluster]
