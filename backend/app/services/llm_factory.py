import os
import json
import re
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel
from openai import OpenAI, AzureOpenAI
from app.config import settings
from app.core.logging import logger

class MockLLMService:
    """
    Intelligent offline/mock LLM engine for development, testing, and zero-cost local execution.
    Analyzes contract text using legal heuristics, regex rules, and predefined playbooks.
    """

    @classmethod
    def generate_summary(cls, contract_text: str) -> Dict[str, Any]:
        # Detect contract type
        lower_text = contract_text.lower()
        if "nondisclosure" in lower_text or "nda" in lower_text or "confidentiality agreement" in lower_text:
            contract_type = "Non-Disclosure Agreement (NDA)"
            title = "Mutual Nondisclosure Agreement"
        elif "software-as-a-service" in lower_text or "saas" in lower_text:
            contract_type = "Software-as-a-Service (SaaS) Agreement"
            title = "Master SaaS Agreement"
        elif "consulting" in lower_text or "services agreement" in lower_text:
            contract_type = "Professional Services Agreement"
            title = "Master Services Agreement"
        else:
            contract_type = "Commercial Contract"
            title = "Commercial Agreement"

        # Detect parties
        parties = []
        party_matches = re.findall(r"(?:between|by and between)\s*[:\s]*([^\n\.,]+(?:\s+Inc\.|\s+LLC|\s+Corp\.|\s+Ltd\.))", contract_text, re.IGNORECASE)
        if party_matches:
            parties = [p.strip() for p in party_matches]
        else:
            # Fallback search for Inc / LLC
            inc_matches = re.findall(r"([A-Z][A-Za-z0-9\s]{2,30}(?:Inc\.|LLC|Ltd\.|Corporation))", contract_text)
            parties = list(dict.fromkeys(inc_matches))[:2] if inc_matches else ["Party A", "Party B"]

        # Detect Governing law
        gov_match = re.search(r"laws of the State of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", contract_text, re.IGNORECASE)
        governing_law = f"State of {gov_match.group(1)}" if gov_match else "State of Delaware (Standard)"

        # Detect dates
        date_match = re.search(r"(?:effective as of|dated as of|Effective Date[\"\s\:\)]+)([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", contract_text, re.IGNORECASE)
        effective_date = date_match.group(1) if date_match else "October 15, 2026"

        return {
            "title": title,
            "contract_type": contract_type,
            "parties": parties,
            "effective_date": effective_date,
            "expiration_date": "1 to 3 Years from Effective Date",
            "governing_law": governing_law,
            "executive_summary": (
                f"This {contract_type} establishes terms and obligations between {', '.join(parties) if parties else 'the parties'}. "
                "The agreement outlines confidential information handling, performance covenants, liability limitations, "
                f"and governing dispute mechanisms in {governing_law}. Critical provisions require close review regarding "
                "indemnification scope and restrictive covenants."
            ),
            "key_obligations": [
                {"party": parties[0] if parties else "Disclosing Party", "obligation": "Protect proprietary confidential materials with reasonable standard of care."},
                {"party": parties[1] if len(parties) > 1 else "Receiving Party", "obligation": "Adhere to restrictive covenants and ensure timely return or destruction upon termination."}
            ]
        }

    @classmethod
    def extract_clauses(cls, contract_text: str) -> List[Dict[str, Any]]:
        clauses = []
        # Patterns for standard legal clauses
        rules = [
            ("Termination", r"(?i)(?:Section\s*\d+[\.:\s]*)?TERMINATION.*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
            ("Confidentiality", r"(?i)(?:Section\s*\d+[\.:\s]*)?CONFIDENTIAL\s+INFORMATION.*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
            ("Limitation of Liability", r"(?i)(?:Section\s*\d+[\.:\s]*)?LIMITATION\s+OF\s+LIABILITY.*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
            ("Indemnification", r"(?i)(?:Section\s*\d+[\.:\s]*)?INDEMNIF(?:ICATION|Y).*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
            ("Governing Law", r"(?i)(?:Section\s*\d+[\.:\s]*)?GOVERNING\s+LAW.*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
            ("Payment Terms", r"(?i)(?:Section\s*\d+[\.:\s]*)?FEES\s+AND\s+PAYMENT.*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
            ("Restrictive Covenants", r"(?i)(?:Section\s*\d+[\.:\s]*)?NON-SOLICITATION.*?(?=\n(?:[A-Z0-9\.\s]{3,30}\n|\Z))"),
        ]

        for clause_type, pattern in rules:
            m = re.search(pattern, contract_text, re.DOTALL)
            if m:
                snippet = m.group(0).strip()
                # Truncate if too huge
                clean_snippet = snippet[:1000]
                clauses.append({
                    "clause_type": clause_type,
                    "section_number": "Identified Section",
                    "title": f"{clause_type} Clause",
                    "clause_text": clean_snippet,
                    "confidence_score": 0.96,
                    "explanation": f"Specifies terms controlling {clause_type.lower()} between the contracting entities."
                })

        if not clauses:
            # Fallback if text format is non-standard
            clauses.append({
                "clause_type": "General Terms",
                "section_number": "1",
                "title": "General Covenants",
                "clause_text": contract_text[:400] + "...",
                "confidence_score": 0.88,
                "explanation": "Primary terms governing party relationship."
            })

        return clauses

    @classmethod
    def analyze_risks(cls, contract_text: str, extracted_clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        lower_text = contract_text.lower()
        risks = []

        # Check 1: Unlimited liability
        if "unlimited" in lower_text or "liability under this agreement is unlimited" in lower_text:
            risks.append({
                "clause_type": "Limitation of Liability",
                "risk_level": "HIGH",
                "issue_description": "Unilateral or uncapped customer liability detected in limitation of liability clause.",
                "impact": "Exposes company to catastrophic financial damage with no upper cap in the event of dispute.",
                "recommendation": "Negotiate a mutual liability cap equal to 12 months fees paid under the contract.",
                "redline_suggestion": "EACH PARTY'S MAXIMUM AGGREGATE LIABILITY SHALL BE CAPPED AT THE TOTAL FEES PAID OR PAYABLE IN THE PRECEDING TWELVE (12) MONTHS."
            })

        # Check 2: Unilateral price increase
        if "increase fees at any time" in lower_text or "reserves the right to increase fees" in lower_text:
            risks.append({
                "clause_type": "Payment Terms",
                "risk_level": "HIGH",
                "issue_description": "Vendor reserves unilateral right to increase fees upon 30 days notice without any cap.",
                "impact": "Unpredictable budget escalation and vendor lock-in.",
                "recommendation": "Cap annual price increases to standard CPI (Consumer Price Index) or maximum 3-5%.",
                "redline_suggestion": "Vendor may increase fees no more than once per renewal term, capped at 3% or the annual CPI increase, with ninety (90) days prior written notice."
            })

        # Check 3: One-sided indemnification
        if "customer shall defend, indemnify" in lower_text and "vendor provides no indemnification" in lower_text:
            risks.append({
                "clause_type": "Indemnification",
                "risk_level": "HIGH",
                "issue_description": "Asymmetric indemnification: Customer provides full indemnity, but Vendor provides zero indemnity for IP infringement.",
                "impact": "Customer assumes entire risk of third-party copyright/patent infringement lawsuits resulting from software use.",
                "recommendation": "Require Vendor to provide full defense and indemnity for third-party IP infringement claims.",
                "redline_suggestion": "Vendor shall defend and indemnify Customer against any third-party claim alleging the Service infringes any patent, copyright, or trademark."
            })

        # Check 4: Restrictive covenants / Non-solicitation
        if "three (3) years" in lower_text and "solicit" in lower_text:
            risks.append({
                "clause_type": "Restrictive Covenants",
                "risk_level": "MEDIUM",
                "issue_description": "Excessive non-solicitation duration (3 years) across all employees and consultants.",
                "impact": "Restricts legitimate hiring practices and general public recruitment postings.",
                "recommendation": "Reduce duration to 1 year and carve out general job advertisements.",
                "redline_suggestion": "Neither party shall solicit employees for a period of one (1) year; provided that general public job advertisements shall not constitute solicitation."
            })

        # Check 5: Auto-renewal with long non-renewal window
        if "automatically renew" in lower_text and "ninety (90) days" in lower_text:
            risks.append({
                "clause_type": "Termination",
                "risk_level": "MEDIUM",
                "issue_description": "Automatic 2-year renewal unless 90 days advance written notice is given.",
                "impact": "Easy to miss the 90-day window resulting in accidental 2-year lock-in.",
                "recommendation": "Reduce notice window to 30 days and require Vendor reminder notice 60 days before expiration.",
                "redline_suggestion": "Agreement renews for 1-year terms unless either party gives thirty (30) days notice. Vendor must notify Customer 60 days before deadline."
            })

        if not risks:
            risks.append({
                "clause_type": "General Assessment",
                "risk_level": "LOW",
                "issue_description": "Standard balanced commercial terms with mutual obligations.",
                "impact": "Low legal exposure under typical commercial conditions.",
                "recommendation": "Ensure internal contract management tracking for milestone and renewal dates.",
                "redline_suggestion": "No critical redline changes required."
            })

        high_count = sum(1 for r in risks if r["risk_level"] == "HIGH")
        overall = "HIGH" if high_count >= 1 else ("MEDIUM" if len(risks) > 1 else "LOW")

        return {
            "overall_risk_score": overall,
            "executive_risk_note": f"Identified {len(risks)} key risk areas ({high_count} HIGH severity). Immediate red-line adjustments recommended before signing.",
            "risks": risks
        }

    @classmethod
    def answer_question(cls, question: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        q_lower = question.lower()
        
        # Pick top chunk as primary citation
        top_chunk = retrieved_chunks[0] if retrieved_chunks else {
            "text": "General contractual provisions apply.",
            "section_number": "1",
            "section_title": "General",
            "page_number": 1
        }

        if "liability" in q_lower or "cap" in q_lower or "damage" in q_lower:
            reply = (
                "Based on the agreement terms, the liability provision specifies financial caps and exclusions. "
                f"Specifically, {top_chunk.get('section_title', 'the liability section')} details the monetary limits "
                "and whether liability is mutual or capped at prior fees."
            )
        elif "terminate" in q_lower or "cancel" in q_lower or "renewal" in q_lower:
            reply = (
                "Regarding termination and term duration, the contract outlines the required notice period "
                f"and renewal clauses in {top_chunk.get('section_title', 'the term section')}. "
                "Notice must be given in writing within the stipulated cure or opt-out window."
            )
        elif "indemn" in q_lower:
            reply = (
                f"Under {top_chunk.get('section_title', 'the indemnification clause')}, the obligation to defend and hold harmless "
                "applies to designated third-party claims, subject to procedural requirements for prompt notification."
            )
        else:
            reply = (
                f"According to the contract provisions retrieved from {top_chunk.get('section_title', 'relevant sections')}, "
                f"the agreement establishes specific covenants governing this issue. The exact excerpt states: "
                f"\"{top_chunk.get('text', '')[:250]}...\""
            )

        citations = [
            {
                "section_number": c.get("section_number", "1"),
                "section_title": c.get("section_title", "Contract Excerpt"),
                "page_number": c.get("page_number", 1),
                "verbatim_quote": c.get("text", "")[:280] + "...",
                "relevance_score": c.get("score", 0.90)
            }
            for c in retrieved_chunks[:3]
        ]

        return {
            "reply": reply,
            "citations": citations
        }


class LLMFactory:
    """
    Factory for instantiating and orchestrating LLM clients (OpenAI, Azure, or Mock).
    """

    @classmethod
    def get_provider(cls) -> str:
        provider = settings.LLM_PROVIDER.lower()
        # If user configured openai but didn't provide key, fallback to mock to prevent crashes
        if provider == "openai" and (not settings.OPENAI_API_KEY or "your_" in settings.OPENAI_API_KEY):
            logger.info("OpenAI API key not set or default; operating in [yellow]MOCK/OFFLINE[/yellow] AI mode.")
            return "mock"
        return provider

    @classmethod
    def get_client(cls):
        provider = cls.get_provider()
        if provider == "openai":
            return OpenAI(api_key=settings.OPENAI_API_KEY)
        elif provider == "azure_openai":
            return AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
        return None
