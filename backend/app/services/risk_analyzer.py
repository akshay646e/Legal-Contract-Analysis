import json
from typing import List, Dict, Any
from app.services.llm_factory import LLMFactory, MockLLMService
from app.config import settings
from app.core.logging import logger

RISK_ANALYSIS_SYSTEM_PROMPT = """
You are an expert Corporate Legal Risk Auditor.
You review commercial agreements to flag unfavorable terms, high financial exposures, missing standard protections, and deviation from balanced corporate playbooks.

For each risk found, evaluate:
- Severity: HIGH, MEDIUM, LOW, or SAFE
- Issue Description: Exactly what makes this clause dangerous or one-sided
- Potential Business Impact
- Actionable Recommendation
- Specific Redline Suggestion (revised balanced clause wording)

Output a JSON object with this exact structure:
{
  "overall_risk_score": "HIGH" | "MEDIUM" | "LOW",
  "executive_risk_note": "Summary of risk posture...",
  "risks": [
    {
      "clause_type": "Limitation of Liability",
      "risk_level": "HIGH",
      "issue_description": "Unilateral customer liability with low vendor cap.",
      "impact": "Uncapped exposure in case of dispute.",
      "recommendation": "Insist on mutual aggregate cap equal to 12 months fees.",
      "redline_suggestion": "EACH PARTY'S AGGREGATE LIABILITY SHALL NOT EXCEED FEES PAID IN PRECEDING 12 MONTHS."
    }
  ]
}

Return ONLY valid JSON.
"""

class RiskAnalyzer:
    @classmethod
    def analyze_risks(cls, contract_text: str, extracted_clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        provider = LLMFactory.get_provider()

        if provider == "mock":
            logger.info("Performing risk analysis using Mock legal playbook.")
            return MockLLMService.analyze_risks(contract_text, extracted_clauses)

        client = LLMFactory.get_client()
        if not client:
            return MockLLMService.analyze_risks(contract_text, extracted_clauses)

        try:
            logger.info("Performing risk analysis via OpenAI...")
            clauses_summary = "\n\n".join([
                f"Clause Type: {c.get('clause_type')}\nText: {c.get('clause_text', '')[:400]}"
                for c in extracted_clauses[:10]
            ])
            sample_text = contract_text[:12000]

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": RISK_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extracted Clauses:\n{clauses_summary}\n\nFull Contract Text Context:\n{sample_text}"}
                ]
            )

            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            return data
        except Exception as e:
            logger.error(f"OpenAI risk analysis failed ({e}). Falling back to heuristic mock.")
            return MockLLMService.analyze_risks(contract_text, extracted_clauses)
