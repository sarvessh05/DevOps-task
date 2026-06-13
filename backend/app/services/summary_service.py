import json
from typing import List, Dict, Any
from app.services.llm_service import LLMService
from app.utils.logger import logger
from app.core.config import settings

class SummaryService:
    @staticmethod
    def _get_fallback_narrative(total_inr: float, total_usd: float, anomaly_count: int) -> Dict[str, Any]:
        """Provides a structured fallback summary when the LLM is unavailable or fails."""
        risk_level = "low"
        if anomaly_count > 0:
            risk_level = "medium" if anomaly_count <= 2 else "high"
            
        return {
            "narrative": f"Processed transactions show a total expenditure of {total_inr:,.2f} INR and {total_usd:,.2f} USD. "
                         f"A total of {anomaly_count} transactions were flagged as anomalous, requiring audit validation.",
            "risk_level": risk_level
        }

    @classmethod
    def generate_summary(cls, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregates transaction stats and requests an AI-generated summary narrative."""
        logger.info("Aggregates transaction stats for narrative summary...")
        
        # 1. Calculate Spend Totals
        total_inr = sum(t["amount"] for t in transactions if t["currency"] == "INR")
        total_usd = sum(t["amount"] for t in transactions if t["currency"] == "USD")
        
        # 2. Calculate Category Breakdown
        # Structure: {"Food": {"INR": 1000.0, "USD": 50.0}, ...}
        category_breakdown: Dict[str, Dict[str, float]] = {}
        for t in transactions:
            cat = t["category"]
            curr = t["currency"]
            amt = t["amount"]
            
            if cat not in category_breakdown:
                category_breakdown[cat] = {"INR": 0.0, "USD": 0.0}
            
            if curr in ("INR", "USD"):
                category_breakdown[cat][curr] += amt
            else:
                if curr not in category_breakdown[cat]:
                    category_breakdown[cat][curr] = 0.0
                category_breakdown[cat][curr] += amt
                
        # 3. Calculate Top Merchants (using a conversion rate of 1 USD = 83 INR for ranking purposes)
        merchant_spend: Dict[str, Dict[str, Any]] = {}
        for t in transactions:
            m = t["merchant"]
            curr = t["currency"]
            amt = t["amount"]
            
            if m not in merchant_spend:
                merchant_spend[m] = {"merchant": m, "spend_inr": 0.0, "spend_usd": 0.0, "ranking_score": 0.0}
                
            if curr == "INR":
                merchant_spend[m]["spend_inr"] += amt
                merchant_spend[m]["ranking_score"] += amt
            elif curr == "USD":
                merchant_spend[m]["spend_usd"] += amt
                merchant_spend[m]["ranking_score"] += amt * 83.0 # convert USD for ranking index
            else:
                merchant_spend[m]["ranking_score"] += amt
                
        # Sort merchants by ranking_score descending and take top 3
        sorted_merchants = sorted(merchant_spend.values(), key=lambda x: x["ranking_score"], reverse=True)
        top_merchants = []
        for m_data in sorted_merchants[:3]:
            top_merchants.append({
                "merchant": m_data["merchant"],
                "spend_inr": round(m_data["spend_inr"], 2),
                "spend_usd": round(m_data["spend_usd"], 2)
            })
            
        # 4. Count Anomalies & Gather Summary list
        anomalies = [t for t in transactions if t["is_anomaly"]]
        anomaly_count = len(anomalies)
        
        anomalies_summary = []
        for a in anomalies[:10]: # limit to first 10 for prompt token safety
            anomalies_summary.append({
                "merchant": a["merchant"],
                "amount": a["amount"],
                "currency": a["currency"],
                "reason": a["anomaly_reason"]
            })
            
        # 5. Generate AI Narrative
        if not settings.GEMINI_API_KEY:
            logger.warning("No Gemini API key available. Generating local fallback summary.")
            ai_data = cls._get_fallback_narrative(total_inr, total_usd, anomaly_count)
        else:
            prompt_payload = {
                "total_spend_inr": total_inr,
                "total_spend_usd": total_usd,
                "top_merchants": top_merchants,
                "anomaly_count": anomaly_count,
                "anomalies": anomalies_summary
            }
            
            prompt = f"""
You are a financial controller analyzing a transaction processing batch.
Generate a concise summary of the following transaction batch data:

{json.dumps(prompt_payload, indent=2)}

Based on the totals, top merchants, and anomalies, return a JSON object with:
1. "narrative": A professional 2-3 sentence spending narrative summarizing key expenditures and trends.
2. "risk_level": A single string rating either "low", "medium", or "high". Assign "high" if there are multiple anomalies or very large unexpected charges, "medium" if there is a single anomaly or minor outliers, and "low" if there are no anomalies.

Return ONLY a JSON object with the keys "narrative" and "risk_level".
Example response:
{{
  "narrative": "Spend was heavily concentrated on domestic travel and retail, with MakeMyTrip and Amazon representing the highest outlay. Two anomalies were detected due to foreign currency billing on domestic food services.",
  "risk_level": "medium"
}}
"""
            try:
                logger.info("Calling Gemini for narrative summary...")
                response_text = LLMService._call_gemini_api(prompt, model_name="gemini-2.5-flash")
                ai_data = json.loads(response_text)
                
                # Check required fields
                if "narrative" not in ai_data or "risk_level" not in ai_data:
                    raise KeyError("Missing required keys in AI response.")
                if ai_data["risk_level"] not in ("low", "medium", "high"):
                    ai_data["risk_level"] = "medium"
                    
            except Exception as e:
                logger.error(f"Failed to generate LLM summary, running fallback: {str(e)}")
                ai_data = cls._get_fallback_narrative(total_inr, total_usd, anomaly_count)
                
        # 6. Construct complete JobSummary object properties
        summary_report = {
            "total_spend_inr": round(total_inr, 2),
            "total_spend_usd": round(total_usd, 2),
            "top_merchants": top_merchants,
            "category_breakdown": category_breakdown,
            "anomaly_count": anomaly_count,
            "narrative": ai_data["narrative"],
            "risk_level": ai_data["risk_level"]
        }
        
        logger.info("Summary report generated successfully.")
        return summary_report
