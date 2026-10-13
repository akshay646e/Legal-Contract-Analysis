import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    status = Column(String(50), default="UPLOADED") # UPLOADED, INDEXED, ANALYZED, FAILED
    total_pages = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    summary = relationship("ContractSummary", back_populates="contract", uselist=False, cascade="all, delete-orphan")
    clauses = relationship("ExtractedClause", back_populates="contract", cascade="all, delete-orphan")
    risks = relationship("RiskFinding", back_populates="contract", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="contract", cascade="all, delete-orphan")


class ContractSummary(Base):
    __tablename__ = "contract_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False, unique=True)
    title = Column(String(255), nullable=True)
    executive_summary = Column(Text, nullable=False)
    contract_type = Column(String(100), nullable=True) # NDA, SaaS, MSA, Employment, etc.
    effective_date = Column(String(100), nullable=True)
    expiration_date = Column(String(100), nullable=True)
    governing_law = Column(String(200), nullable=True)
    parties = Column(Text, nullable=True) # JSON string or comma-separated
    key_obligations = Column(Text, nullable=True) # JSON formatted string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract = relationship("Contract", back_populates="summary")


class ExtractedClause(Base):
    __tablename__ = "extracted_clauses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    clause_type = Column(String(100), nullable=False, index=True) # Termination, Indemnity, Liability, etc.
    section_number = Column(String(50), nullable=True)
    title = Column(String(255), nullable=True)
    clause_text = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.95)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract = relationship("Contract", back_populates="clauses")
    risks = relationship("RiskFinding", back_populates="clause", cascade="all, delete-orphan")


class RiskFinding(Base):
    __tablename__ = "risk_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    clause_id = Column(Integer, ForeignKey("extracted_clauses.id"), nullable=True)
    clause_type = Column(String(100), nullable=False)
    risk_level = Column(String(20), nullable=False, index=True) # HIGH, MEDIUM, LOW, SAFE
    issue_description = Column(Text, nullable=False)
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=False)
    redline_suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract = relationship("Contract", back_populates="risks")
    clause = relationship("ExtractedClause", back_populates="risks")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False) # user or assistant
    message = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=True) # JSON string of citation snippets & page refs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract = relationship("Contract", back_populates="chat_messages")
