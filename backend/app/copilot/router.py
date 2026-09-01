import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.copilot.schemas import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotHealthResponse,
)
from app.copilot.service import CopilotService, history_manager
from app.copilot.ollama import ollama_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
async def chat_with_copilot(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sends a security question to the Guardrail AI Copilot with contextual repository grounding.
    """
    try:
        return await CopilotService.chat(
            db=db,
            user_id=current_user.id,
            request=request,
        )
    except ValueError as e:
        # Resource not found or tenant access denied
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error in chat_with_copilot: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your Copilot request.",
        )


@router.get("/health", response_model=CopilotHealthResponse)
async def get_copilot_health(
    current_user: User = Depends(get_current_user),
):
    """
    Checks the connectivity and status of the local Ollama AI model service.
    """
    return await ollama_client.check_health()


@router.post("/clear-history")
def clear_copilot_history(
    current_user: User = Depends(get_current_user),
):
    """
    Clears the short-term in-memory conversation history for the current user.
    """
    history_manager.clear(str(current_user.id))
    return {"message": "Copilot conversation history cleared successfully."}
