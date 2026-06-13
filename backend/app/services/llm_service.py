import json
from typing import List, Dict, Any
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import logger

# Configure Gemini API
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not configured. LLM classification will fail gracefully.")

ALLOWED_CATEGORIES = [
    "Food",
    "Shopping",
    "Travel",
    "Transport",
    "Utilities",
    "Cash Withdrawal",
    "Entertainment",
    "Other"
]

class LLMService:
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_gemini_api(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
        """Helper to invoke Gemini API with retries and structured output."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key is missing.")
            
        # Try using gemini-2.5-flash first, fall back to gemini-1.5-flash if needed
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except Exception as e:
            # If 2.5-flash fails due to model availability, try 1.5-flash
            if model_name == "gemini-2.5-flash":
                logger.warning(f"Failed to use gemini-2.5-flash, falling back to gemini-1.5-flash: {str(e)}")
                return LLMService._call_gemini_api(prompt, model_name="gemini-1.5-flash")
            raise e

    @classmethod
    def classify_batch(cls, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classifies a single batch of up to 20 transactions using Gemini."""
        if not settings.GEMINI_API_KEY:
            logger.error("Skipping LLM batch classification: GEMINI_API_KEY is unset.")
            for txn in batch:
                txn["llm_failed"] = True
                txn["category"] = "UNCATEGORIZED"
            return batch

        # Build structured payload for the LLM
        prompt_data = []
        for idx, txn in enumerate(batch):
            prompt_data.append({
                "temp_id": idx,
                "merchant": txn["merchant"],
                "notes": txn["notes"] or ""
            })
            
        prompt = f"""
You are an expert financial transaction classification assistant.
Classify each transaction in the JSON list into exactly ONE of these categories:
{', '.join(ALLOWED_CATEGORIES)}

Input data:
{json.dumps(prompt_data, indent=2)}

Return ONLY a JSON array containing objects with keys "temp_id" and "category".
Ensure "category" exactly matches one of the values listed above.
Example response:
[
  {{"temp_id": 0, "category": "Food"}},
  {{"temp_id": 1, "category": "Shopping"}}
]
"""
        try:
            logger.info(f"Calling Gemini API to classify a batch of {len(batch)} transactions...")
            # We try gemini-2.5-flash as requested by user, falling back to 1.5-flash if needed
            response_text = cls._call_gemini_api(prompt, model_name="gemini-2.5-flash")
            response_data = json.loads(response_text)
            
            # Map categories back
            category_map = {item["temp_id"]: item["category"] for item in response_data if "temp_id" in item}
            
            for idx, txn in enumerate(batch):
                category = category_map.get(idx)
                if category in ALLOWED_CATEGORIES:
                    txn["category"] = category
                    txn["llm_category"] = category
                    txn["llm_failed"] = False
                else:
                    txn["category"] = "Other"
                    txn["llm_category"] = "Other"
                    txn["llm_failed"] = False
                    
            logger.info("Batch classification completed successfully.")
            
        except Exception as e:
            logger.error(f"Gemini batch classification failed after retries: {str(e)}")
            # Mark all as failed in this batch
            for txn in batch:
                txn["llm_failed"] = True
                txn["category"] = "UNCATEGORIZED"
                
        return batch

    @classmethod
    def classify_transactions(cls, transactions: List[Dict[str, Any]], batch_size: int = 20) -> List[Dict[str, Any]]:
        """Splits uncategorized transactions into batches of size N and processes them."""
        # Find transactions needing classification (those with category = UNCATEGORIZED)
        uncategorized_indices = [
            i for i, txn in enumerate(transactions) 
            if txn["category"] == "UNCATEGORIZED"
        ]
        
        if not uncategorized_indices:
            logger.info("No uncategorized transactions found. Skipping LLM classification.")
            return transactions
            
        logger.info(f"Found {len(uncategorized_indices)} transactions requiring AI classification.")
        
        # Batch and process
        for i in range(0, len(uncategorized_indices), batch_size):
            batch_indices = uncategorized_indices[i:i + batch_size]
            batch_txns = [transactions[idx] for idx in batch_indices]
            
            classified_batch = cls.classify_batch(batch_txns)
            
            # Write results back to the master list
            for idx, cleaned_txn in zip(batch_indices, classified_batch):
                transactions[idx] = cleaned_txn
                
        return transactions
