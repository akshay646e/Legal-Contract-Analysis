from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RiskFindingItem(BaseModel):
    clause_type: str = Field(description="The clause type evaluated, e.g. Limitation of Liability, Termination, Indemnity")
    risk_level: str = Field(description="Risk severity level: HIGH, MEDIUM, LOW, or SAFE")
    issue_description: str = Field(description="Specific legal risk or unfair commercial term identified")
    impact: Optional[str] = Field(default=None, description="Potential business, financial, or legal exposure to the organization")
    recommendation: str = Field(description="Actionable guidance on how to negotiate or remediate this risk")
    redline_suggestion: Optional[str] = Field(default=None, description="Proposed alternative wording / mark-up clause to counter-offer")

class RiskAnalysisExtraction(BaseModel):
    overall_risk_score: str = Field(description="Overall risk rating of agreement: HIGH, MEDIUM, or LOW")
    executive_risk_note: str = Field(description="High-level risk summary for leadership")
    risks: List[RiskFindingItem] = Field(default_factory=list, description="Detailed list of specific risk items")

class RiskFindingResponse(RiskFindingItem):
    id: int
    contract_id: str
    clause_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
