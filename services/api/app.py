from fastapi import FastAPI
import logging
from ..ingestion_service.main import make_job
# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(title="GenAI Error Log Inspector")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest/run")
def ingest_run():
    logger.info("Received request: /ingest/run")
    
    try:
        logger.info("Creating job...")
        job = make_job()
        logger.info("Job created, executing...")
        
        job()  # this runs the ingestion task
        
        logger.info("Job finished successfully")
        return {"status": "completed"}
    except Exception as e:
        logger.exception("Error while running job")
        return {"status": "error", "detail": str(e)}
