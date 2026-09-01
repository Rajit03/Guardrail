import re
import logging
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.core.config import settings
from app.copilot.schemas import CopilotHealthResponse

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with local Ollama instance.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> CopilotHealthResponse:
        """
        Verifies if Ollama is reachable and the configured model is installed.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return CopilotHealthResponse(
                        status="UNAVAILABLE",
                        reachable=False,
                        model_available=False,
                        model_name=self.model,
                        message="Guardrail Copilot is unavailable because the local AI model service returned an error.",
                    )

                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Check exact or prefix match (e.g. 'llama3.2:1b' in models)
                model_found = any(
                    self.model == m or self.model == m.split(":")[0] or m.startswith(self.model)
                    for m in models
                )

                if not model_found:
                    return CopilotHealthResponse(
                        status="MODEL_MISSING",
                        reachable=True,
                        model_available=False,
                        model_name=self.model,
                        message=f"Configured Ollama model '{self.model}' is not installed in local Ollama.",
                    )

                return CopilotHealthResponse(
                    status="HEALTHY",
                    reachable=True,
                    model_available=True,
                    model_name=self.model,
                    message=f"Ollama is operational with model '{self.model}'.",
                )

        except httpx.ConnectError:
            return CopilotHealthResponse(
                status="UNREACHABLE",
                reachable=False,
                model_available=False,
                model_name=self.model,
                message="Guardrail Copilot is unavailable because the local AI model cannot be reached.",
            )
        except httpx.TimeoutException:
            return CopilotHealthResponse(
                status="TIMEOUT",
                reachable=False,
                model_available=False,
                model_name=self.model,
                message="Guardrail Copilot connection timed out while checking model health.",
            )
        except Exception as e:
            logger.warning(f"Ollama health check error: {type(e).__name__}")
            return CopilotHealthResponse(
                status="ERROR",
                reachable=False,
                model_available=False,
                model_name=self.model,
                message="Guardrail Copilot is unavailable because the local AI model is not reachable.",
            )

    async def chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> Tuple[str, List[str]]:
        """
        Sends conversation messages to Ollama `/api/chat` and returns (answer, recommended_actions).
        """
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            formatted_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": 0.2,  # Low temperature for deterministic security explanations
                "top_p": 0.9,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                if resp.status_code == 404:
                    raise ValueError(f"Configured Ollama model '{self.model}' is not available.")
                if resp.status_code != 200:
                    raise RuntimeError(f"Ollama returned HTTP status {resp.status_code}")

                data = resp.json()
                raw_response = data.get("message", {}).get("content", "").strip()

                if not raw_response:
                    return (
                        "Guardrail Copilot analyzed your request but received an empty response. Please review the findings below.",
                        [],
                    )

                # Extract actions and clean response
                answer, actions = self._parse_response_actions(raw_response)
                return answer, actions

        except httpx.ConnectError:
            raise ConnectionError("Guardrail Copilot is unavailable because the local AI model cannot be reached.")
        except httpx.TimeoutException:
            raise TimeoutError("Copilot took too long to respond. Please try again.")

    def _parse_response_actions(self, text: str) -> Tuple[str, List[str]]:
        """
        Parses recommended action items from the model's text output if present.
        """
        actions: List[str] = []
        lines = text.split("\n")
        
        # Look for bullet points under recommendation headers
        in_recs = False
        for line in lines:
            trimmed = line.strip()
            if re.search(r'(?i)(recommend|action|steps? to fix|how to remediate|remediation)', trimmed):
                in_recs = True
                continue
            if in_recs:
                match = re.match(r'^[-*•\d\.]+\s+(.+)$', trimmed)
                if match:
                    act = match.group(1).strip()
                    if act and len(act) > 5 and len(act) < 250:
                        actions.append(act)
                elif trimmed == "" and actions:
                    in_recs = False

        # Fallback if no specific section was detected but bullet points exist at bottom
        if not actions:
            for line in lines[-8:]:
                trimmed = line.strip()
                match = re.match(r'^[-*•\d\.]+\s+(.+)$', trimmed)
                if match:
                    act = match.group(1).strip()
                    if act and len(act) > 10 and len(act) < 250:
                        actions.append(act)

        # Clean answer text
        answer = text.strip()
        # Cap actions at 5
        actions = actions[:5]

        return answer, actions


ollama_client = OllamaClient()
