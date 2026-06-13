import os
from datetime import datetime
import uuid
from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary
from app.services.csv_processor import CSVProcessor
from app.services.anomaly_detector import AnomalyDetector
from app.services.llm_service import LLMService
from app.services.summary_service import SummaryService
from app.utils.logger import logger

@celery_app.task(name="app.workers.tasks.process_csv_task", bind=True)
def process_csv_task(self, job_id_str: str, file_path: str):
    """Asynchronously cleans, classifies, and aggregates a transaction CSV file."""
    logger.info(f"Task started for job {job_id_str} using file: {file_path}")
    
    db = SessionLocal()
    job_uuid = uuid.UUID(job_id_str)
    
    try:
        # 1. Fetch Job and set status to processing
        job = db.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            logger.error(f"Job {job_id_str} not found in DB.")
            return False
            
        job.status = "processing"
        job.progress = 10
        db.commit()
        
        # 2. Read File Bytes
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Uploaded file not found at {file_path}")
            
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        # 3. Clean Transactions
        cleaned_txns, raw_count, clean_count = CSVProcessor.clean_transactions(file_bytes)
        
        # Update Row Counts and Progress
        job.row_count_raw = raw_count
        job.row_count_clean = clean_count
        job.progress = 30
        db.commit()
        
        # 4. Anomaly Detection
        cleaned_txns = AnomalyDetector.detect_anomalies(cleaned_txns, db)
        job.progress = 50
        db.commit()
        
        # 5. LLM Classification (Batched)
        cleaned_txns = LLMService.classify_transactions(cleaned_txns, batch_size=20)
        job.progress = 80
        db.commit()
        
        # 6. LLM Summary Narrative & Spend Metrics
        summary_report = SummaryService.generate_summary(cleaned_txns)
        job.progress = 95
        db.commit()
        
        # 7. Persist Transactions
        db_txns = []
        for t in cleaned_txns:
            db_txn = Transaction(
                job_id=job_uuid,
                txn_id=t["txn_id"],
                date=t["date"],
                merchant=t["merchant"],
                amount=t["amount"],
                currency=t["currency"],
                status=t["status"],
                category=t["category"],
                account_id=t["account_id"],
                notes=t["notes"],
                is_anomaly=t["is_anomaly"],
                anomaly_reason=t["anomaly_reason"],
                llm_category=t["llm_category"],
                llm_failed=t["llm_failed"]
            )
            db_txns.append(db_txn)
            
        db.add_all(db_txns)
        
        # 8. Persist Job Summary
        db_summary = JobSummary(
            job_id=job_uuid,
            total_spend_inr=summary_report["total_spend_inr"],
            total_spend_usd=summary_report["total_spend_usd"],
            top_merchants=summary_report["top_merchants"],
            category_breakdown=summary_report["category_breakdown"],
            anomaly_count=summary_report["anomaly_count"],
            narrative=summary_report["narrative"],
            risk_level=summary_report["risk_level"]
        )
        db.add(db_summary)
        
        # 9. Finalize Job
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Job {job_id_str} processed successfully!")
        
        # Cleanup uploaded file from volume storage
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temp upload file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not delete temp file {file_path}: {str(e)}")
            
        return True
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Error processing job {job_id_str}: {str(e)}")
        
        # Update Job to failed status
        try:
            job = db.query(Job).filter(Job.id == job_uuid).first()
            if job:
                job.status = "failed"
                job.progress = 100
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as rollback_err:
            logger.error(f"Failed to record job failure state in DB: {str(rollback_err)}")
            
        return False
        
    finally:
        db.close()
