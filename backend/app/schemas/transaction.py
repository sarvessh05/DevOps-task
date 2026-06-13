from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date as dt_date

class TransactionResponse(BaseModel):
    id: UUID
    txn_id: Optional[str] = None
    date: Optional[dt_date] = None
    merchant: str
    amount: float
    currency: str
    status: str
    category: str
    account_id: str
    notes: Optional[str] = None
    is_anomaly: bool
    anomaly_reason: Optional[str] = None
    llm_category: Optional[str] = None
    llm_failed: bool

    class Config:
        from_attributes = True

class MerchantSpend(BaseModel):
    merchant: str
    spend_inr: float
    spend_usd: float

class FullJobSummary(BaseModel):
    total_spend_inr: float
    total_spend_usd: float
    top_merchants: List[MerchantSpend]
    category_breakdown: Dict[str, Dict[str, float]]
    anomaly_count: int
    narrative: Optional[str] = None
    risk_level: Optional[str] = None

class JobResultsResponse(BaseModel):
    summary: Optional[FullJobSummary] = None
    anomalies: List[TransactionResponse]
    transactions: List[TransactionResponse]

    class Config:
        from_attributes = True
