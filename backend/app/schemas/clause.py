from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ClauseItem(BaseModel):
    clause_type: str = Field(description="Category of clause, e.g., Termination, Indemnity, Limitation of Liability, Payment Terms, Confidentiality, Governing Law, Non-Compete, Force Majeure")
    section_number: Optional[str] = Field(default=None, description="Section or paragraph number in the contract, e.g., 'Section 4' or '4.2'")
    title: Optional[str] = Field(default=None, description="Heading of the clause if available")
    clause_text: str = Field(description="The exact or verbatim text of the clause extracted from the agreement")
    confidence_score: float = Field(default=0.95, description="Model extraction confidence score (0.0 to 1.0)")
    explanation: Optional[str] = Field(default=None, description="Brief explanation of what this clause entails in plain English")

class ClauseListExtraction(BaseModel):
    clauses: List[ClauseItem] = Field(default_factory=list, description="Extracted legal clauses from the agreement")

class ClauseResponse(ClauseItem):
    id: int
    contract_id: str
    created_at: datetime

    class Config:
        from_attributes = True
