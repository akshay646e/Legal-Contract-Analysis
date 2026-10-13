from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ContractBase(BaseModel):
    filename: str
    file_type: str
    file_size_bytes: int

class ContractCreate(ContractBase):
    pass

class ContractResponse(ContractBase):
    id: str
    status: str
    total_pages: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContractStats(BaseModel):
    total_contracts: int
    analyzed_contracts: int
    total_clauses_extracted: int
    high_risks_detected: int
