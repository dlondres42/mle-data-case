"""Orchestrates the extraction flow: preprocess -> prompt -> LLM -> parse."""

import json

from app.schemas.incident import IncidentInfo
from app.services.llm import LLMClient
from app.services.preprocessing import preprocess
from app.services.prompts import build_extraction_prompt

# Strings some models emit instead of a JSON null for absent information.
_NULL_SENTINELS = {"", "null", "none", "n/a", "nao informado", "não informado"}


def _clean_value(value: object) -> str | None:
    text = str(value).strip()
    if text.casefold() in _NULL_SENTINELS:
        return None
    return text


def parse_llm_response(raw: str) -> IncidentInfo:
    """Parse the model output into IncidentInfo, tolerating noisy responses.

    Small models often wrap the JSON in extra text, so we take the outermost
    {...} block. Anything unparseable degrades to an all-null IncidentInfo
    rather than an error, since model quality is not this API's contract.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end <= start:
        return IncidentInfo()
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return IncidentInfo()
    if not isinstance(data, dict):
        return IncidentInfo()

    fields = {
        name: cleaned
        for name in IncidentInfo.model_fields
        if (value := data.get(name)) is not None
        and (cleaned := _clean_value(value)) is not None
    }
    return IncidentInfo(**fields)


def extract_incident(text: str, llm: LLMClient) -> IncidentInfo:
    clean_text = preprocess(text)
    prompt = build_extraction_prompt(clean_text)
    raw_response = llm.generate(prompt)
    return parse_llm_response(raw_response)
