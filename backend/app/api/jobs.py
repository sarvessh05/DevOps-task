import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.summary import JobSummary
from app.schemas.job import JobCreateResponse, JobStatusResponse, JobListResponse, JobSummaryStats
from app.schemas.transaction import JobResultsResponse, TransactionResponse, FullJobSummary
from app.workers.tasks import process_csv_task
from app.utils.logger import logger

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/upload", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Uploads a transaction CSV file, creates a Job record, and enqueues the processing pipeline."""
    # 1. File type validation
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files (.csv) are accepted."
        )

    # 2. Create Job in database
    job_id = uuid.uuid4()
    db_job = Job(
        id=job_id,
        filename=file.filename,
        status="pending",
        progress=0
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    logger.info(f"Created job {job_id} for file {file.filename}")

    # 3. Save uploaded file to the shared volume directory
    temp_filename = f"{job_id}.csv"
    temp_filepath = os.path.join(settings.UPLOAD_DIR, temp_filename)
    
    try:
        with open(temp_filepath, "wb") as buffer:
            # Read in chunks to prevent large memory spikes
            while content := await file.read(1024 * 1024):  # 1MB chunk size
                buffer.write(content)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        db_job.status = "failed"
        db_job.progress = 100
        db_job.error_message = f"Failed to save file: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving uploaded file."
        )

    # 4. Trigger Celery Task asynchronously
    try:
        process_csv_task.delay(str(job_id), temp_filepath)
        logger.info(f"Enqueued background task for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to enqueue Celery task: {str(e)}")
        db_job.status = "failed"
        db_job.progress = 100
        db_job.error_message = f"Failed to queue task: {str(e)}"
        db.commit()
        # Clean up temp file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task runner error: {str(e)}"
        )

    return {"job_id": job_id, "status": "pending"}

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Returns the current progress, status, and high-level stats of a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
        
    summary_stats = None
    if job.status == "completed" and job.summary:
        summary_stats = JobSummaryStats(
            total_spend_inr=job.summary.total_spend_inr,
            total_spend_usd=job.summary.total_spend_usd,
            anomaly_count=job.summary.anomaly_count,
            risk_level=job.summary.risk_level
        )
        
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        row_count_raw=job.row_count_raw,
        row_count_clean=job.row_count_clean,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        summary=summary_stats
    )

@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Fetches the aggregated analysis results, category breakdowns, anomalies list, and clean transaction logs."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
        
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job processing is not complete yet. Current status: {job.status}"
        )
        
    # Get summary
    summary_data = None
    if job.summary:
        summary_data = FullJobSummary(
            total_spend_inr=job.summary.total_spend_inr,
            total_spend_usd=job.summary.total_spend_usd,
            top_merchants=[m for m in job.summary.top_merchants],
            category_breakdown=job.summary.category_breakdown,
            anomaly_count=job.summary.anomaly_count,
            narrative=job.summary.narrative,
            risk_level=job.summary.risk_level
        )
        
    # Query transactions
    txns = db.query(Transaction).filter(Transaction.job_id == job_id).all()
    anomalies = [t for t in txns if t.is_anomaly]
    
    return JobResultsResponse(
        summary=summary_data,
        anomalies=[TransactionResponse.model_validate(a) for a in anomalies],
        transactions=[TransactionResponse.model_validate(t) for t in txns]
    )

@router.get("", response_model=List[JobListResponse])
def list_jobs(
    status: Optional[str] = Query(None, description="Filter jobs by status (e.g. pending, completed, failed)"),
    db: Session = Depends(get_db)
):
    """Retrieves all jobs in reverse chronological order, optionally filtered by status."""
    query = select(Job)
    if status:
        query = query.where(Job.status == status.lower())
        
    query = query.order_by(Job.created_at.desc())
    jobs = db.scalars(query).all()
    
    return [JobListResponse.model_validate(j) for j in jobs]
