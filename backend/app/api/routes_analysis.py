import json
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.parsers.document_parser import DocumentParser
from app.services.summarizer import ContractSummarizer
from app.services.clause_extractor import ClauseExtractor
from app.services.risk_analyzer import RiskAnalyzer
from app.schemas.summary import ContractSummaryResponse
from app.schemas.clause import ClauseResponse
from app.schemas.risk import RiskFindingResponse
from app.core.logging import logger

router = APIRouter(prefix="/api/analysis", tags=["Contract Analysis & AI Insights"])

def _get_contract_text(contract: models.Contract) -> str:
    if not os.path.exists(contract.storage_path):
        raise HTTPException(status_code=404, detail="Contract file missing from storage.")
    parsed = DocumentParser.parse_file(contract.storage_path)
    return parsed.full_text

@router.post("/{contract_id}/summarize")
def summarize_contract(contract_id: str, db: Session = Depends(get_db)):
    """Generates an executive summary and key obligations."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    text = _get_contract_text(contract)
    summary_data = ContractSummarizer.summarize(text)

    # Save or update summary in DB
    existing_summary = db.query(models.ContractSummary).filter(models.ContractSummary.contract_id == contract_id).first()
    if existing_summary:
        db.delete(existing_summary)
        db.commit()

    parties_str = ", ".join(summary_data.get("parties", []))
    obligations_json = json.dumps(summary_data.get("key_obligations", []))

    db_summary = models.ContractSummary(
        contract_id=contract_id,
        title=summary_data.get("title"),
        contract_type=summary_data.get("contract_type"),
        executive_summary=summary_data.get("executive_summary", ""),
        effective_date=summary_data.get("effective_date"),
        expiration_date=summary_data.get("expiration_date"),
        governing_law=summary_data.get("governing_law"),
        parties=parties_str,
        key_obligations=obligations_json
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return summary_data


@router.post("/{contract_id}/clauses")
def extract_contract_clauses(contract_id: str, db: Session = Depends(get_db)):
    """Extracts critical clauses (Termination, Indemnity, Liability, etc.)."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    text = _get_contract_text(contract)
    clauses_data = ClauseExtractor.extract_clauses(text)

    # Clear old clauses for this contract
    db.query(models.ExtractedClause).filter(models.ExtractedClause.contract_id == contract_id).delete()
    db.commit()

    saved_clauses = []
    for c in clauses_data:
        clause_obj = models.ExtractedClause(
            contract_id=contract_id,
            clause_type=c.get("clause_type", "General"),
            section_number=c.get("section_number"),
            title=c.get("title"),
            clause_text=c.get("clause_text", ""),
            confidence_score=c.get("confidence_score", 0.95),
            explanation=c.get("explanation")
        )
        db.add(clause_obj)
        saved_clauses.append(clause_obj)

    db.commit()
    return {"contract_id": contract_id, "clauses": clauses_data}


@router.post("/{contract_id}/risks")
def analyze_contract_risks(contract_id: str, db: Session = Depends(get_db)):
    """Performs risk audit, severity categorization, and redline suggestions."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    text = _get_contract_text(contract)

    # Get extracted clauses if available
    db_clauses = db.query(models.ExtractedClause).filter(models.ExtractedClause.contract_id == contract_id).all()
    clauses_payload = [
        {"clause_type": c.clause_type, "clause_text": c.clause_text}
        for c in db_clauses
    ]

    risk_analysis = RiskAnalyzer.analyze_risks(text, clauses_payload)

    # Clear old risks
    db.query(models.RiskFinding).filter(models.RiskFinding.contract_id == contract_id).delete()
    db.commit()

    for r in risk_analysis.get("risks", []):
        risk_obj = models.RiskFinding(
            contract_id=contract_id,
            clause_type=r.get("clause_type", "General"),
            risk_level=r.get("risk_level", "MEDIUM"),
            issue_description=r.get("issue_description", ""),
            impact=r.get("impact"),
            recommendation=r.get("recommendation", ""),
            redline_suggestion=r.get("redline_suggestion")
        )
        db.add(risk_obj)

    contract.status = "ANALYZED"
    db.commit()

    return risk_analysis


@router.post("/{contract_id}/full-pipeline")
def run_full_pipeline(contract_id: str, db: Session = Depends(get_db)):
    """Runs summarization, clause extraction, and risk analysis sequentially."""
    logger.info(f"Running full automated AI pipeline on contract [yellow]{contract_id}[/yellow]")
    summary = summarize_contract(contract_id, db)
    clauses = extract_contract_clauses(contract_id, db)
    risks = analyze_contract_risks(contract_id, db)

    return {
        "contract_id": contract_id,
        "status": "COMPLETED",
        "summary": summary,
        "clauses": clauses.get("clauses", []),
        "risks": risks
    }


@router.get("/{contract_id}/results")
def get_analysis_results(contract_id: str, db: Session = Depends(get_db)):
    """Fetches stored summary, clauses, and risk findings for a contract."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    summary_record = db.query(models.ContractSummary).filter(models.ContractSummary.contract_id == contract_id).first()
    clauses_records = db.query(models.ExtractedClause).filter(models.ExtractedClause.contract_id == contract_id).all()
    risks_records = db.query(models.RiskFinding).filter(models.RiskFinding.contract_id == contract_id).all()

    summary_data = None
    if summary_record:
        summary_data = {
            "title": summary_record.title,
            "contract_type": summary_record.contract_type,
            "executive_summary": summary_record.executive_summary,
            "parties": [p.strip() for p in summary_record.parties.split(",")] if summary_record.parties else [],
            "effective_date": summary_record.effective_date,
            "expiration_date": summary_record.expiration_date,
            "governing_law": summary_record.governing_law,
            "key_obligations": json.loads(summary_record.key_obligations) if summary_record.key_obligations else []
        }

    clauses_data = [
        {
            "id": c.id,
            "clause_type": c.clause_type,
            "section_number": c.section_number,
            "title": c.title,
            "clause_text": c.clause_text,
            "confidence_score": c.confidence_score,
            "explanation": c.explanation
        }
        for c in clauses_records
    ]

    risks_data = [
        {
            "id": r.id,
            "clause_type": r.clause_type,
            "risk_level": r.risk_level,
            "issue_description": r.issue_description,
            "impact": r.impact,
            "recommendation": r.recommendation,
            "redline_suggestion": r.redline_suggestion
        }
        for r in risks_records
    ]

    return {
        "contract_id": contract_id,
        "filename": contract.filename,
        "status": contract.status,
        "summary": summary_data,
        "clauses": clauses_data,
        "risks": risks_data
    }
