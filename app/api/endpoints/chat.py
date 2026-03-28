from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated

from app.db.database import get_db
from app.models import models
from app.services.ai_engine import GeminiInterpreter
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat with Gemini"])
db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/ask")
async def chat_with_chart(
    profile_id: int,
    question: str,
    db: db_dependency,
    current_user: models.User = Depends(get_current_user),
):
    profile = (
        db.query(models.Profile)
        .filter(
            models.Profile.id == profile_id,
            models.Profile.user_id == current_user.id,
        )
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    analysis = (
        db.query(models.Analysis)
        .filter(models.Analysis.profile_id == profile_id)
        .order_by(models.Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this profile")

    past_messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.analysis_id == analysis.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )

    formatted_history = [{"role": msg.role, "parts": [msg.content]} for msg in past_messages]

    interpreter = GeminiInterpreter()
    try:
        answer = interpreter.answer_question(
            chart_data=analysis.chart_data,
            report=analysis.report_content,
            question=question,
            history=formatted_history,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e!s}")

    user_msg = models.ChatMessage(analysis_id=analysis.id, role="user", content=question)
    model_msg = models.ChatMessage(analysis_id=analysis.id, role="model", content=answer)

    try:
        db.add(user_msg)
        db.add(model_msg)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save chat messages.")

    return {"answer": answer}
