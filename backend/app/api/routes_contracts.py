import os
import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.schemas.contract import ContractResponse, ContractStats
from app.parsers.document_parser import DocumentParser
from app.rag.chunker import LegalContractChunker
from app.rag.vector_store import vector_store
from app.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/api/contracts", tags=["Contracts Management"])

@router.post("/upload", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a legal contract (PDF, DOCX, or TXT), parses its text and structure,
    stores metadata in SQLite/PostgreSQL, and indexes chunks into the Vector DB.
    """
    filename = file.filename or "contract.txt"
    suffix = Path(filename).suffix.lower()

    if suffix not in [".pdf", ".docx", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{suffix}'. Supported formats: .pdf, .docx, .txt"
        )

    contract_id = str(uuid.uuid4())
    save_dir = Path(settings.UPLOAD_DIRECTORY)
    save_dir.mkdir(parents=True, exist_ok=True)
    saved_file_path = save_dir / f"{contract_id}_{filename}"

    # Save uploaded file to disk
    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded contract.")

    file_size = os.path.getsize(saved_file_path)

    # 1. Parse document text and sections
    try:
        parsed_doc = DocumentParser.parse_file(str(saved_file_path))
    except Exception as e:
        logger.error(f"Parsing error on {filename}: {e}")
        raise HTTPException(status_code=422, detail=f"Document parsing error: {str(e)}")

    # 2. Chunk document using section-aware legal chunker
    chunker = LegalContractChunker()
    chunks = chunker.chunk_document(parsed_doc, contract_id=contract_id)

    # 3. Index chunks into vector store
    vector_store.add_chunks(contract_id=contract_id, chunks=chunks)

    # 4. Save contract record to Database
    db_contract = models.Contract(
        id=contract_id,
        filename=filename,
        file_type=parsed_doc.file_type,
        file_size_bytes=file_size,
        storage_path=str(saved_file_path),
        total_pages=parsed_doc.total_pages,
        status="INDEXED"
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)

    logger.info(f"Successfully processed and indexed contract: [green]{filename}[/green] ({contract_id}) with {len(chunks)} chunks.")
    return db_contract


@router.get("", response_model=List[ContractResponse])
def list_contracts(db: Session = Depends(get_db)):
    """Lists all contracts uploaded to the system."""
    contracts = db.query(models.Contract).order_by(models.Contract.created_at.desc()).all()
    return contracts


@router.get("/{contract_id}")
def get_contract_detail(contract_id: str, db: Session = Depends(get_db)):
    """Retrieves contract metadata and raw text content."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Read original text if available
    raw_text = ""
    if os.path.exists(contract.storage_path):
        try:
            parsed = DocumentParser.parse_file(contract.storage_path)
            raw_text = parsed.full_text
        except Exception:
            raw_text = "Content preview currently unavailable."

    return {
        "id": contract.id,
        "filename": contract.filename,
        "file_type": contract.file_type,
        "file_size_bytes": contract.file_size_bytes,
        "status": contract.status,
        "total_pages": contract.total_pages,
        "created_at": contract.created_at,
        "full_text": raw_text
    }


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    """Deletes a contract, its analysis artifacts, and vector embeddings."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Remove file from disk
    if os.path.exists(contract.storage_path):
        try:
            os.remove(contract.storage_path)
        except Exception as e:
            logger.warning(f"Failed to delete file from disk: {e}")

    # Remove from vector store
    vector_store.delete_contract(contract_id)

    # Delete database record
    db.delete(contract)
    db.commit()
    logger.info(f"Deleted contract [red]{contract_id}[/red]")
    return None


@router.get("/stats/overview", response_model=ContractStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Returns high-level statistics for executive dashboard metrics."""
    total = db.query(models.Contract).count()
    analyzed = db.query(models.Contract).filter(models.Contract.status == "ANALYZED").count()
    clauses = db.query(models.ExtractedClause).count()
    high_risks = db.query(models.RiskFinding).filter(models.RiskFinding.risk_level == "HIGH").count()

    return ContractStats(
        total_contracts=total,
        analyzed_contracts=analyzed,
        total_clauses_extracted=clauses,
        high_risks_detected=high_risks
    )
