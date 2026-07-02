from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.incident import ExtractRequest, IncidentInfo
from app.services.extraction import extract_incident
from app.services.llm import LLMClient, LLMUnavailableError, OllamaClient

router = APIRouter(tags=["extraction"])


def get_llm_client() -> LLMClient:
    return OllamaClient(format_schema=IncidentInfo.model_json_schema())


@router.post("/extract")
def extract(
    request: ExtractRequest,
    llm: Annotated[LLMClient, Depends(get_llm_client)],
) -> IncidentInfo:
    try:
        return extract_incident(request.texto, llm)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"LLM indisponível: {exc}") from exc
