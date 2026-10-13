import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryItem
from app.services.qa_service import ContractQAService
from app.core.logging import logger

router = APIRouter(prefix="/api/chat", tags=["Contract RAG Q&A"])

@router.post("", response_model=ChatResponse)
def ask_contract_question(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Asks a question about a specific contract using grounded RAG.
    Returns the answer and verifiable citation quotes with section and page numbers.
    """
    contract = db.query(models.Contract).filter(models.Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Save User message in DB
    user_msg = models.ChatMessage(
        contract_id=request.contract_id,
        role="user",
        message=request.message,
        citations_json=None
    )
    db.add(user_msg)
    db.commit()

    # Run RAG QA service
    result = ContractQAService.ask(
        contract_id=request.contract_id,
        question=request.message
    )

    reply_text = result.get("reply", "")
    citations = result.get("citations", [])

    # Save Assistant message in DB
    asst_msg = models.ChatMessage(
        contract_id=request.contract_id,
        role="assistant",
        message=reply_text,
        citations_json=json.dumps(citations)
    )
    db.add(asst_msg)
    db.commit()

    return ChatResponse(
        contract_id=request.contract_id,
        reply=reply_text,
        citations=citations
    )


@router.get("/{contract_id}/history", response_model=List[ChatHistoryItem])
def get_chat_history(contract_id: str, db: Session = Depends(get_db)):
    """Retrieves conversation history and citations for a contract."""
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.contract_id == contract_id
    ).order_by(models.ChatMessage.created_at.asc()).all()

    history = []
    for m in messages:
        cites = json.loads(m.citations_json) if m.citations_json else []
        history.append(ChatHistoryItem(
            id=m.id,
            role=m.role,
            message=m.message,
            citations=cites,
            created_at=m.created_at
        ))

    return history
