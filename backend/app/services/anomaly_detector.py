import statistics
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.transaction import Transaction
from app.utils.logger import logger

# List of domestic-only merchants specified in the assignment or found in the dataset
DOMESTIC_MERCHANTS = {"SWIGGY", "OLA", "IRCTC"}

class AnomalyDetector:
    @staticmethod
    def detect_anomalies(transactions: List[Dict[str, Any]], db: Session) -> List[Dict[str, Any]]:
        """Processes transaction records to identify statistical and structural anomalies.
        
        Rule 1: Flag if amount > 3x the account's median spend.
        Rule 2: Flag if merchant is domestic-only (Swiggy, Ola, IRCTC) and currency is USD.
        """
        logger.info("Running anomaly detection rules...")
        
        # Group current batch transactions by account_id to optimize database queries
        current_by_account: Dict[str, List[Dict[str, Any]]] = {}
        for txn in transactions:
            acc_id = txn["account_id"]
            if acc_id not in current_by_account:
                current_by_account[acc_id] = []
            current_by_account[acc_id].append(txn)
            
        # Process each account's transactions
        for acc_id, txns_list in current_by_account.items():
            # 1. Fetch historical amounts for this account from the database
            try:
                stmt = select(Transaction.amount).where(Transaction.account_id == acc_id)
                historical_amounts = db.scalars(stmt).all()
            except Exception as e:
                logger.error(f"Error fetching historical amounts for account {acc_id}: {str(e)}")
                historical_amounts = []
                
            # Combine historical amounts with the current batch amounts
            current_amounts = [t["amount"] for t in txns_list]
            combined_amounts = list(historical_amounts) + current_amounts
            
            # Calculate median
            if combined_amounts:
                median_amount = statistics.median(combined_amounts)
            else:
                median_amount = 0.0
                
            logger.info(f"Account {acc_id}: Median spend is {median_amount:.2f} (from {len(combined_amounts)} transactions)")
            
            # 2. Apply rules
            for txn in txns_list:
                reasons = []
                
                # Rule 1: Outlier check (> 3x median)
                # Avoid flagging very small amounts as anomalies (e.g. median is 10, amount is 40)
                # Let's say if amount > 3 * median AND amount > 500 (or just apply the rule strictly)
                # The assignment says: "amount exceeds 3x the account's median as a statistical outlier"
                # Let's check: if median is greater than 0, we check.
                if median_amount > 0 and txn["amount"] > 3 * median_amount:
                    reasons.append(f"Amount {txn['amount']:.2f} exceeds 3x the account's median of {median_amount:.2f}")
                    
                # Rule 2: Domestic Merchant with USD
                merchant_upper = txn["merchant"].upper()
                if merchant_upper in DOMESTIC_MERCHANTS and txn["currency"] == "USD":
                    reasons.append(f"Domestic merchant '{txn['merchant']}' billed in foreign currency ({txn['currency']})")
                    
                # Combine reasons if any
                if reasons:
                    txn["is_anomaly"] = True
                    txn["anomaly_reason"] = " | ".join(reasons)
                    logger.warning(f"Anomaly detected in txn: {txn.get('txn_id', 'SYNTH')} - Reason: {txn['anomaly_reason']}")
                    
        return transactions
