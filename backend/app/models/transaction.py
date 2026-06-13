import uuid
from sqlalchemy import Column, String, Float, Boolean, Text, ForeignKey, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    txn_id = Column(String(100), nullable=True)
    date = Column(Date, nullable=True)
    merchant = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False, default="UNCATEGORIZED")
    account_id = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Anomaly tracking
    is_anomaly = Column(Boolean, default=False, nullable=False)
    anomaly_reason = Column(Text, nullable=True)
    
    # LLM classification tracking
    llm_category = Column(String(100), nullable=True)
    llm_failed = Column(Boolean, default=False, nullable=False)

    # Relationships
    job = relationship("Job", back_populates="transactions")

    # Indexes for performance
    __table_args__ = (
        Index("idx_transactions_job_id", "job_id"),
        Index("idx_transactions_account_id", "account_id"),
    )
