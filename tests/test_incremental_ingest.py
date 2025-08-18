import os
from pathlib import Path
from services.ingestion_service.ingestors.local_ingestor import LocalIngestor

def test_incremental(tmp_path):
    log = tmp_path/"error-2025-08-13.log"
    log.write_text("INFO ok\nERROR bad1\n", encoding="utf-8")
    ing = LocalIngestor()
    lines = list(ing.incremental_read(str(log), 0, r"ERROR", None))
    assert len(lines) == 1
    # append
    with log.open("a", encoding="utf-8") as f:
        f.write("ERROR bad2\n")
    # start from prior offset
    last_offset = lines[-1][1]
    lines2 = list(ing.incremental_read(str(log), last_offset, r"ERROR", None))
    assert len(lines2) == 1
