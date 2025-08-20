# services/ingestion_service/state_manager.py

import mysql.connector
from mysql.connector import Error
import json
import os
import datetime
import logging


class StateManager:
    """
    Tracks file offsets in MySQL so ingestion can resume from last processed point.
    Also logs ingestion executions with metadata.
    """

    def __init__(self, db_cfg: dict, debug: int = 0, log_dir: str = "logs"):
        self.db_cfg = db_cfg
        self.debug = debug
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        print("DB CONFIG:", self.db_cfg)
        # Setup logger
         # Create logger for this class
        self.logger = logging.getLogger("StateManager")
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(os.path.join(self.log_dir, "state_manager.log"))
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if debug else logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

          # Add handler only if not already added
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        self.logger.info("Initialized StateManager with DB config: %s", self.db_cfg)
        self._ensure_tables()

    def _get_conn(self):
        print("DB CONFIG 123:", self.db_cfg)
        return mysql.connector.connect(
            host=self.db_cfg["host"],
            port=self.db_cfg["port"],
            user=self.db_cfg["user"],
            password=self.db_cfg["password"],
            database=self.db_cfg["database"],
            ssl_disabled=True
        )


    def _ensure_tables(self):
        """
        Ensure required tables exist.
        """
        create_offsets = """
        CREATE TABLE IF NOT EXISTS log_offsets (
            cluster_name   VARCHAR(255) NOT NULL,
            log_type       VARCHAR(255) NOT NULL,
            file_key       VARCHAR(255) NOT NULL,
            offset_val     BIGINT NOT NULL,
            PRIMARY KEY (cluster_name, log_type, file_key)
        )
        """
        create_executions = """
        CREATE TABLE IF NOT EXISTS execution_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            run_time DATETIME NOT NULL,
            execution_time FLOAT,
            execution_interval INT,
            status VARCHAR(50),
            payload_json JSON,
            response_json JSON
        )
        """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_offsets)
                    cur.execute(create_executions)
                conn.commit()
        except Error as e:
            print(f"[StateManager] Error creating table: {e}")
            raise

    def get_offset1(self, cluster_name: str, log_type: str, file_key: str) -> int:
        self.logger.debug("Anish Rai")
        """
        Returns last saved offset or 0 if not found.
        """
        sql = """
        SELECT offset_val FROM log_offsets
        WHERE cluster_name = %s AND log_type = %s AND file_key = %s
        """
        try:
            self.logger.debug("Executing Anis SQL: %s | values=%s", sql.strip(), (cluster_name, log_type, file_key))
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    self.logger.debug("Executing SQL: %s | values=%s", sql.strip(), (cluster_name, log_type, file_key))
                    cur.execute(sql, (cluster_name, log_type, file_key))
                    row = cur.fetchone()
                    return row[0] if row else 0
        except Error as e:
            self.logger.error("Error reading offset: %s", e)
            print(f"[StateManager] Error reading offset: {e}")
            return 0
     
    def get_offset(self, cluster_name: str, log_type: str, file_key: str) -> int:
        self.logger.debug("Entering get_offset()")
        sql = """
        SELECT offset_val FROM log_offsets
        WHERE cluster_name = %s AND log_type = %s AND file_key = %s
        """
        try:
            self.logger.debug("Executing SQL: %s | values=%s", sql.strip(), (cluster_name, log_type, file_key))
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (cluster_name, log_type, file_key))
                    row = cur.fetchone()
                    self.logger.debug("Fetched row: %s", row)
                    #return row[0] if row else 0
                    return 111
        except Error as e:
            self.logger.error("Error reading offset: %s", e)
            return 0
 
    def upsert_offset(self, cluster_name: str, log_type: str, file_key: str, offset_val: int):
        """
        Inserts or updates offset for given file.
        """
        sql = """
        INSERT INTO log_offsets (cluster_name, log_type, file_key, offset_val)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE offset_val = VALUES(offset_val)
        """
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (cluster_name, log_type, file_key, offset_val))
                conn.commit()
        except Error as e:
            print(f"[StateManager] Error writing offset: {e}")

# ---------------- Execution Logging ---------------- #
    def log_execution(
        self,
        execution_time: float,
        execution_interval: int,
        status: str,
        payload: dict = None,
        response: dict = None
    ):
        """
        Logs each run of ingestion into MySQL and optional file.
        """
        run_time = datetime.datetime.now()
        payload_json = json.dumps(payload or {})
        response_json = json.dumps(response or {})

        sql = """
        INSERT INTO execution_log (run_time, execution_time, execution_interval, status, payload_json, response_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        # Print the SQL with parameters
        print("[StateManager] Executing SQL:", sql.strip())
        print("[StateManager] With values:", values)
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (run_time, execution_time, execution_interval, status, payload_json, response_json))
                conn.commit()
        except Error as e:
            print(f"[StateManager] Error writing execution log: {e}")

        # Optional debug log to file
        if self.debug:
            log_file = os.path.join(self.log_dir, f"execution_{run_time.date()}.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"[{run_time}] status={status}, "
                    f"execution_time={execution_time}s, interval={execution_interval}s\n"
                    f"payload={payload_json}\nresponse={response_json}\n\n"
                )

        # Always print if no logs were found
        if status.lower() == "no_new_logs":
            print(f"[ExecutionLog] {run_time}: No new log entries detected.")



