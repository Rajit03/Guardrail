import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.copilot.schemas import (
    CopilotChatRequest,
    CopilotChatResponse,
    RelatedFindingItem,
    ConversationMessage,
)
from app.copilot.security import is_secret_exfiltration_attempt
from app.copilot.prompts import (
    SYSTEM_PROMPT,
    SECRET_REFUSAL_RESPONSE,
    build_user_prompt,
)
from app.copilot.context import SecurityContextBuilder
from app.copilot.ollama import ollama_client

logger = logging.getLogger(__name__)


class CopilotRateLimiter:
    """
    In-memory rate limiter tracking requests per user in a 1-hour window.
    """
    def __init__(self, limit_per_hour: int = 30):
        self.limit = limit_per_hour
        self.user_requests = defaultdict(list)

    def is_rate_limited(self, user_id: str) -> bool:
        now = time.time()
        window_start = now - 3600  # 1 hour
        # Purge older timestamps
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if t > window_start]
        if len(self.user_requests[user_id]) >= self.limit:
            return True
        self.user_requests[user_id].append(now)
        return False


class CopilotHistoryManager:
    """
    In-memory short-term conversation history per user session (capped at MAX_HISTORY_MESSAGES).
    """
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.histories: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return list(self.histories[user_id])

    def add_turn(self, user_id: str, user_msg: str, assistant_msg: str) -> None:
        hist = self.histories[user_id]
        hist.append({"role": "user", "content": user_msg})
        hist.append({"role": "assistant", "content": assistant_msg})
        if len(hist) > self.max_messages:
            self.histories[user_id] = hist[-self.max_messages:]

    def clear(self, user_id: str) -> None:
        self.histories.pop(user_id, None)


rate_limiter = CopilotRateLimiter(limit_per_hour=settings.COPILOT_RATE_LIMIT_PER_HOUR)
history_manager = CopilotHistoryManager(max_messages=settings.MAX_HISTORY_MESSAGES)


class CopilotService:
    @staticmethod
    async def chat(
        db: Session,
        user_id: uuid.UUID | str,
        request: CopilotChatRequest,
    ) -> CopilotChatResponse:
        str_uid = str(user_id)

        # 1. Rate Limiting Check
        if rate_limiter.is_rate_limited(str_uid):
            return CopilotChatResponse(
                answer="You have reached the hourly Copilot request limit (30 requests/hour). Please try again later.",
                recommended_actions=["Wait for your rate limit window to reset before asking additional questions."],
                related_findings=[],
                model_used=settings.OLLAMA_MODEL,
            )

        # 2. Secret Query Shield Check (exfiltration prevention)
        if is_secret_exfiltration_attempt(request.message):
            logger.info(f"Secret exfiltration attempt shielded for user {str_uid}")
            return CopilotChatResponse(
                answer=SECRET_REFUSAL_RESPONSE["answer"],
                recommended_actions=SECRET_REFUSAL_RESPONSE["recommended_actions"],
                related_findings=[],
                model_used=settings.OLLAMA_MODEL,
            )

        # 3. Build Security Context & Related Findings
        try:
            context_data, related_findings, intent = SecurityContextBuilder.build_context(
                db=db,
                user_id=user_id,
                query=request.message,
                repository_id=request.repository_id,
                finding_id=request.finding_id,
                scan_id=request.scan_id,
            )
        except ValueError as e:
            # Ownership / invalid ID error
            raise e

        # 4. Construct Prompt
        user_prompt_content = build_user_prompt(
            user_query=request.message,
            context_data=context_data,
            intent=intent,
        )

        # Prepare messages including short-term history
        history = history_manager.get_history(str_uid)
        current_messages = history + [{"role": "user", "content": user_prompt_content}]

        # 5. Call Ollama
        try:
            start_t = time.time()
            answer, actions = await ollama_client.chat(
                system_prompt=SYSTEM_PROMPT,
                messages=current_messages,
            )
            latency = time.time() - start_t
            logger.info(f"Copilot chat completed for user {str_uid} in {latency:.2f}s (model={settings.OLLAMA_MODEL})")

            # Fallback recommendations if model didn't extract any but findings exist
            if not actions and related_findings:
                actions = CopilotService._generate_fallback_actions(related_findings)

            # Record turn in short-term history
            history_manager.add_turn(str_uid, request.message, answer)

            return CopilotChatResponse(
                answer=answer,
                recommended_actions=actions,
                related_findings=related_findings,
                context_summary={
                    "intent": intent,
                    "findings_count": len(related_findings),
                    "overall_score": context_data.get("overall_security", {}).get("security_score"),
                },
                model_used=settings.OLLAMA_MODEL,
            )

        except ConnectionError:
            logger.warning("Ollama connection error during Copilot chat")
            return CopilotService._fallback_deterministic_response(
                intent, context_data, related_findings,
                "Guardrail Copilot is unavailable because the local AI model cannot be reached."
            )
        except TimeoutError:
            logger.warning("Ollama timeout during Copilot chat")
            return CopilotService._fallback_deterministic_response(
                intent, context_data, related_findings,
                "Copilot took too long to respond. Below is the verified Guardrail security summary."
            )
        except Exception as e:
            logger.error(f"Unexpected error in Copilot service: {type(e).__name__}: {str(e)}")
            return CopilotService._fallback_deterministic_response(
                intent, context_data, related_findings,
                f"Copilot encountered an error communicating with model '{settings.OLLAMA_MODEL}'. Below is your Guardrail security analysis."
            )

    @staticmethod
    def _generate_fallback_actions(findings: List[RelatedFindingItem]) -> List[str]:
        actions = []
        has_secret = any(f.type == "SECRET" for f in findings)
        has_dep = any(f.type == "DEPENDENCY" for f in findings)

        if has_secret:
            actions.append("Rotate and revoke exposed credentials immediately at the provider.")
            actions.append("Remove sensitive tokens and password files from git history.")
        if has_dep:
            actions.append("Upgrade vulnerable packages to their respective fixed versions.")
            actions.append("Run package test suites to verify compatibility after upgrades.")
        actions.append("Trigger a new Guardrail scan to verify all remediation actions.")
        return actions[:4]

    @staticmethod
    def _fallback_deterministic_response(
        intent: str,
        context_data: Dict[str, Any],
        related_findings: List[RelatedFindingItem],
        notice: str,
    ) -> CopilotChatResponse:
        """
        Provides a structured, factual fallback response directly from Guardrail data
        when the local Ollama instance is offline or timing out.
        """
        sec_info = context_data.get("overall_security", {})
        score = sec_info.get("security_score", 100)
        rating = sec_info.get("rating", "Excellent")
        risk_lvl = sec_info.get("risk_level", "LOW")

        if not related_findings:
            answer = (
                f"{notice}\n\n"
                f"**Current Security Status:**\n"
                f"- Security Score: **{score}/100** ({rating}, {risk_lvl} risk)\n"
                f"- Guardrail did not detect active security issues using the currently enabled scanners."
            )
            actions = ["Maintain security by keeping dependency manifests updated and running periodic scans."]
        else:
            top_f = related_findings[0]
            answer = (
                f"{notice}\n\n"
                f"**Current Security Status:**\n"
                f"- Security Score: **{score}/100** ({rating}, {risk_lvl} risk)\n"
                f"- Total Active Findings: **{len(related_findings)}**\n\n"
                f"**Highest Priority Finding:**\n"
                f"- **{top_f.title}** ({top_f.severity} severity, Risk Score: {top_f.risk_score}, Priority: {top_f.priority})\n"
                f"- Location: `{top_f.file_path or top_f.package_name or 'N/A'}`\n"
                f"- Type: {top_f.type}"
            )
            actions = CopilotService._generate_fallback_actions(related_findings)

        return CopilotChatResponse(
            answer=answer,
            recommended_actions=actions,
            related_findings=related_findings,
            context_summary={
                "intent": intent,
                "findings_count": len(related_findings),
                "fallback": True,
            },
            model_used=settings.OLLAMA_MODEL,
        )
