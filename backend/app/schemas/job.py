from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class JobSummaryStats(BaseModel):
    total_spend_inr: float
    total_spend_usd: float
    anomaly_count: int
    risk_level: Optional[str] = None

class JobCreateResponse(BaseModel):
    job_id: UUID
    status: str

class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    progress: int
    row_count_raw: int
    row_count_clean: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    summary: Optional[JobSummaryStats] = None

    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    row_count_raw: int
    row_count_clean: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
