from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    texto: str = Field(min_length=1, description="Free-text incident description")


class IncidentInfo(BaseModel):
    data_ocorrencia: str | None = None
    local: str | None = None
    tipo_incidente: str | None = None
    impacto: str | None = None
