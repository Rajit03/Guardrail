from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service Health Check")
def health_check():
    """Return health status of the Guardrail API service."""
    return {
        "status": "ok",
        "service": "guardrail-api"
    }
