import json
from typing import Dict, Any
from app.services.llm_factory import LLMFactory, MockLLMService
from app.config import settings
from app.core.logging import logger

SUMMARIZE_SYSTEM_PROMPT = """
You are a Senior Legal Counsel and Contract Intelligence AI.
Analyze the provided legal contract and output a rigorous JSON object matching this schema:
{
  "title": "Title of contract",
  "contract_type": "NDA / SaaS / MSA / Consulting / Employment / Commercial",
  "executive_summary": "Concise 2-3 paragraph plain-English executive summary highlighting core business purpose, deal structure, and critical risk areas.",
  "parties": ["Party A full legal entity", "Party B full legal entity"],
  "effective_date": "Date string or None",
  "expiration_date": "Term length or expiration date",
  "governing_law": "Jurisdiction and State",
  "key_obligations": [
    {"party": "Party Name", "obligation": "Specific commitment or deliverable"}
  ]
}

Return ONLY valid JSON.
"""

class ContractSummarizer:
    @classmethod
    def summarize(cls, contract_text: str) -> Dict[str, Any]:
        provider = LLMFactory.get_provider()
        
        if provider == "mock":
            logger.info("Generating contract summary using Mock legal analyzer.")
            return MockLLMService.generate_summary(contract_text)

        client = LLMFactory.get_client()
        if not client:
            return MockLLMService.generate_summary(contract_text)

        try:
            logger.info("Generating contract summary via OpenAI...")
            # Limit prompt text if contract is excessively long for summary
            sample_text = contract_text[:12000]
            
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Legal Contract Text:\n\n{sample_text}"}
                ]
            )

            raw_json = response.choices[0].message.content
            data = json.loads(raw_json)
            return data
        except Exception as e:
            logger.error(f"OpenAI summarization failed ({e}). Falling back to heuristic mock.")
            return MockLLMService.generate_summary(contract_text)
