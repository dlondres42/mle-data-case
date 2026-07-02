from fastapi import FastAPI

from app.routes import extract, health

app = FastAPI(
    title="Incident Extraction API",
    description="Extracts structured incident data from free text using a local LLM.",
)

app.include_router(health.router)
app.include_router(extract.router)
