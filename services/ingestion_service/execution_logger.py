import os
import json
import time
import mysql.connector
from datetime import datetime
from mysql.connector import Error

class ExecutionLogger:
    def __init__(self, db_config: dict, log_file: str = "execution.log", debug: bool = False):
        self.db_config = db_config
        self.log_file = log_file
        self.debug = debug

        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def _connect_db(self):
        """Create DB connection (short-lived, per log)."""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as e:
            print(f"[ExecutionLogger] DB connection failed: {e}")
            return None

    def log_run(self, start_time: float, payload: dict, response: dict, status: str):
        """Log summary of ingestion run to DB + file."""
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        interval = f"{execution_time} sec"

        record = {
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time": execution_time,
            "execution_interval": interval,
            "status": status,
            "payload": json.dumps(payload),
            "response": json.dumps(response),
        }

        # 1. Save to DB
        conn = self._connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ingestion_runs (run_time, execution_time, execution_interval, status, payload, response)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    record["time"],
                    record["execution_time"],
                    record["execution_interval"],
                    record["status"],
                    record["payload"],
                    record["response"],
                ))
                conn.commit()
            except Error as e:
                print(f"[ExecutionLogger] Failed to insert into DB: {e}")
            finally:
                conn.close()

        # 2. Save to text file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record) + "\n")

    def log_entry(self, entry: dict):
        """Log every single log entry (only if debug=1)."""
        if not self.debug:
            return

        line = {
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "entry": entry,
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(line) + "\n")
