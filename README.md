# GenAI Error Log Inspector
######
genai-error-log-inspector/
├── docker/
│   ├── postgres/
│   └── redis/
├── services/
│   ├── ingestion_service/
│   │   ├── __init__.py
│   │   ├── main.py                # CLI / service entry
│   │   ├── config.py
│   │   ├── cluster_manager.py     # selects clusters (SRP)
│   │   ├── ingestors/
│   │   │   ├── base.py            # Ingestor interface
│   │   │   ├── sftp_ingestor.py
│   │   │   ├── http_ingestor.py
│   │   │   └── syslog_ingestor.py
│   │   ├── parser/
│   │   │   ├── base_parser.py
│   │   │   └── regex_parser.py
│   │   └── scheduler.py
│   ├── analysis_service/
│   │   ├── __init__.py
│   │   ├── pipeline.py            # LangGraph orchestration wrapper
│   │   ├── retriever.py
│   │   ├── llm_client.py          # OpenAI wrapper
│   │   └── enricher.py
│   ├── api/
│   │   ├── app.py                 # FastAPI app: endpoints for status, configs, re-run
│   │   └── schemas.py
│   └── notifications/
│       ├── notifier.py            # Notifier interface + implementations
│
├── tests/
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── Dockerfile                    # for the main service
├── requirements.txt
├── pyproject.toml / setup.cfg
├── README.md
└── docs/
    ├── architecture.md
    └── runbook.md

######