import uuid
from sqlalchemy import Column, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    total_spend_inr = Column(Float, default=0.0, nullable=False)
    total_spend_usd = Column(Float, default=0.0, nullable=False)
    top_merchants = Column(JSON, default=list, nullable=False)        # List of dicts: [{"merchant": "Amazon", "spend_inr": 10000}, ...]
    category_breakdown = Column(JSON, default=dict, nullable=False)  # Dict: {"Food": {"INR": 1000.0, "USD": 50.0}, ...}
    anomaly_count = Column(Integer, default=0, nullable=False)
    
    narrative = Column(Text, nullable=True)
    risk_level = Column(Text, nullable=True) # "low", "medium", "high"

    # Relationships
    job = relationship("Job", back_populates="summary")
