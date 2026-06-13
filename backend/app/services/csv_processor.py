import io
from datetime import datetime
from typing import Tuple, List, Dict, Any
import pandas as pd
from app.utils.logger import logger

def normalize_date(date_val: Any) -> Any:
    """Normalizes various date formats to a datetime.date object.
    Supports DD-MM-YYYY, YYYY/MM/DD, and YYYY-MM-DD.
    """
    if pd.isna(date_val) or not str(date_val).strip():
        return None
    
    date_str = str(date_val).strip()
    
    # Try different formats
    for fmt in ("%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
            
    logger.warning(f"Could not parse date string: {date_str}. Storing as Null.")
    return None

def clean_amount(amount_val: Any) -> float:
    """Cleans currency prefixes (like '$') and converts to float."""
    if pd.isna(amount_val) or not str(amount_val).strip():
        return 0.0
    
    amount_str = str(amount_val).strip()
    # Strip common currency signs and whitespace
    cleaned = amount_str.replace('$', '').replace('€', '').replace('£', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Failed to parse amount: {amount_str}. Defaulting to 0.0")
        return 0.0

class CSVProcessor:
    @staticmethod
    def clean_transactions(file_bytes: bytes) -> Tuple[List[Dict[str, Any]], int, int]:
        """Cleans and normalizes transactions from raw CSV bytes.
        
        Returns:
            Tuple: (List of cleaned transaction dicts, raw_row_count, clean_row_count)
        """
        logger.info("Starting CSV data cleaning and normalization...")
        
        # Read CSV bytes using Pandas
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            logger.error(f"Error reading CSV bytes: {str(e)}")
            raise ValueError(f"Invalid CSV format: {str(e)}")
            
        raw_row_count = len(df)
        logger.info(f"Loaded CSV with {raw_row_count} raw rows.")
        
        # 1. Drop exact duplicate rows
        df = df.drop_duplicates()
        dedup_row_count = len(df)
        logger.info(f"Duplicates removed. Row count dropped from {raw_row_count} to {dedup_row_count}.")
        
        cleaned_transactions = []
        
        for idx, row in df.iterrows():
            # Extract and normalize values
            txn_id = str(row.get('txn_id')).strip() if not pd.isna(row.get('txn_id')) else None
            # If txn_id is 'nan' or empty string, convert to None
            if txn_id in ('nan', '', 'None'):
                txn_id = None
                
            raw_date = row.get('date')
            normalized_date = normalize_date(raw_date)
            
            merchant = str(row.get('merchant', 'Unknown')).strip()
            
            raw_amount = row.get('amount')
            cleaned_val_amount = clean_amount(raw_amount)
            
            currency = str(row.get('currency', 'INR')).strip().upper()
            if currency in ('NAN', 'NONE', ''):
                currency = 'INR'
                
            status = str(row.get('status', 'PENDING')).strip().upper()
            if status in ('NAN', 'NONE', ''):
                status = 'PENDING'
                
            category = str(row.get('category', '')).strip()
            if not category or category.upper() in ('NAN', 'NONE', 'NULL', ''):
                category = 'UNCATEGORIZED'
                
            account_id = str(row.get('account_id', 'ACC_UNKNOWN')).strip()
            notes = str(row.get('notes', '')).strip() if not pd.isna(row.get('notes')) else None
            if notes in ('nan', '', 'None'):
                notes = None
                
            cleaned_row = {
                "txn_id": txn_id,
                "date": normalized_date,
                "merchant": merchant,
                "amount": cleaned_val_amount,
                "currency": currency,
                "status": status,
                "category": category,
                "account_id": account_id,
                "notes": notes,
                "is_anomaly": False,
                "anomaly_reason": None,
                "llm_category": None,
                "llm_failed": False
            }
            cleaned_transactions.append(cleaned_row)
            
        clean_row_count = len(cleaned_transactions)
        logger.info(f"Data cleaning finished. Clean row count: {clean_row_count}")
        return cleaned_transactions, raw_row_count, clean_row_count
