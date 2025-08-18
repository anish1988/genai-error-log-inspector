CREATE TABLE IF NOT EXISTS processed_logs (
  cluster_name VARCHAR(255) NOT NULL,
  log_type     VARCHAR(255) NOT NULL,
  file_name    VARCHAR(255) NOT NULL,
  last_position BIGINT DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (cluster_name, log_type, file_name)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_time DATETIME NOT NULL,
    execution_time FLOAT NOT NULL,
    execution_interval VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    payload JSON,
    response JSON
);

