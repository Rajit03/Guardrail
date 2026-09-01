import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question or prompt for the Copilot")
    repository_id: Optional[str] = Field(None, description="Optional target repository UUID")
    finding_id: Optional[str] = Field(None, description="Optional target finding UUID")
    scan_id: Optional[str] = Field(None, description="Optional target scan UUID")


class RelatedFindingItem(BaseModel):
    id: uuid.UUID | str
    title: str
    severity: str
    risk_score: int = 0
    priority: str = "P3"
    type: str
    file_path: Optional[str] = None
    package_name: Optional[str] = None
    vulnerability_id: Optional[str] = None


class CopilotChatResponse(BaseModel):
    answer: str
    recommended_actions: List[str] = Field(default_factory=list)
    related_findings: List[RelatedFindingItem] = Field(default_factory=list)
    context_summary: Optional[Dict[str, Any]] = None
    model_used: str = "llama3.2:1b"


class CopilotHealthResponse(BaseModel):
    status: str
    reachable: bool
    model_available: bool
    model_name: str
    message: str


class ConversationMessage(BaseModel):
    role: str  # 'user', 'assistant', or 'system'
    content: str
