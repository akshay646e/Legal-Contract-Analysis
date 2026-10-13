import json
from typing import List, Dict, Any
from app.services.llm_factory import LLMFactory, MockLLMService
from app.config import settings
from app.core.logging import logger

CLAUSE_EXTRACTION_SYSTEM_PROMPT = """
You are an expert Legal Tech AI specialized in Contract Lifecycle Management (CLM).
Your job is to identify and extract key legal clauses from commercial agreements.

Look for the following clause categories:
1. Termination (convenience, cause, notice periods)
2. Confidentiality (scope, duration, exceptions)
3. Limitation of Liability (monetary caps, indirect damage disclaimers, mutual/unilateral)
4. Indemnification (third-party claims, scope, IP carveouts)
5. Payment Terms (invoicing, late fees, price escalation)
6. Governing Law & Jurisdiction (state/country, venue, dispute forum)
7. Restrictive Covenants (non-solicitation, non-compete)
8. Intellectual Property (ownership, licenses, data usage)

Output a JSON object with this exact structure:
{
  "clauses": [
    {
      "clause_type": "Limitation of Liability",
      "section_number": "Section 6",
      "title": "LIMITATION OF LIABILITY",
      "clause_text": "Verbatim quote of the clause text...",
      "confidence_score": 0.98,
      "explanation": "Clear explanation of what this clause means and its operational impact."
    }
  ]
}

Return ONLY valid JSON.
"""

class ClauseExtractor:
    @classmethod
    def extract_clauses(cls, contract_text: str) -> List[Dict[str, Any]]:
        provider = LLMFactory.get_provider()

        if provider == "mock":
            logger.info("Extracting clauses using Mock legal extractor.")
            return MockLLMService.extract_clauses(contract_text)

        client = LLMFactory.get_client()
        if not client:
            return MockLLMService.extract_clauses(contract_text)

        try:
            logger.info("Extracting clauses via OpenAI...")
            sample_text = contract_text[:14000]

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": CLAUSE_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract all critical clauses from this contract:\n\n{sample_text}"}
                ]
            )

            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            return data.get("clauses", [])
        except Exception as e:
            logger.error(f"OpenAI clause extraction failed ({e}). Falling back to heuristic mock.")
            return MockLLMService.extract_clauses(contract_text)
