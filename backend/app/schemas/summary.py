from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class KeyObligation(BaseModel):
    party: str = Field(description="Name of the party responsible (e.g. Vendor, Customer, Apex)")
    obligation: str = Field(description="Description of the specific requirement, deliverable, or commitment")

class ContractSummaryExtraction(BaseModel):
    title: str = Field(description="Formal title or type of contract")
    contract_type: str = Field(description="NDA, SaaS, Master Services Agreement, Vendor, Employment, etc.")
    executive_summary: str = Field(description="Concise 2-3 paragraph plain-English executive summary of the agreement")
    parties: List[str] = Field(default_factory=list, description="Names of all contracting parties")
    effective_date: Optional[str] = Field(default=None, description="Effective Date of agreement")
    expiration_date: Optional[str] = Field(default=None, description="Expiration or termination date / duration")
    governing_law: Optional[str] = Field(default=None, description="Jurisdiction and governing law state/country")
    key_obligations: List[KeyObligation] = Field(default_factory=list, description="List of primary party obligations")

class ContractSummaryResponse(BaseModel):
    id: int
    contract_id: str
    title: Optional[str]
    contract_type: Optional[str]
    executive_summary: str
    effective_date: Optional[str]
    expiration_date: Optional[str]
    governing_law: Optional[str]
    parties: Optional[List[str]] = []
    key_obligations: Optional[List[KeyObligation]] = []
    created_at: datetime

    class Config:
        from_attributes = True
