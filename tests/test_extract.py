import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.extract import get_llm_client
from app.services.llm import LLMUnavailableError


class FakeLLM:
    """Stub that satisfies the LLMClient Protocol with a canned response."""

    def __init__(self, response: str = "{}"):
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class DownLLM:
    def generate(self, prompt: str) -> str:
        raise LLMUnavailableError("connection refused")


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def override_llm(llm):
    app.dependency_overrides[get_llm_client] = lambda: llm


def test_extract_happy_path(client):
    override_llm(
        FakeLLM(
            '{"data_ocorrencia": "2025-08-12 14:00", "local": "São Paulo",'
            ' "tipo_incidente": "Falha no servidor", "impacto": "Faturamento parado"}'
        )
    )

    response = client.post("/extract", json={"texto": "Ontem às 14h em São Paulo..."})

    assert response.status_code == 200
    assert response.json() == {
        "data_ocorrencia": "2025-08-12 14:00",
        "local": "São Paulo",
        "tipo_incidente": "Falha no servidor",
        "impacto": "Faturamento parado",
    }


def test_extract_preprocesses_text_before_prompting(client):
    fake = FakeLLM()
    override_llm(fake)

    client.post("/extract", json={"texto": "  falha \n\n no  servidor "})

    assert len(fake.prompts) == 1
    assert "falha no servidor" in fake.prompts[0]


def test_extract_with_noisy_llm_output_still_returns_json(client):
    override_llm(FakeLLM('Claro! Aqui está: {"local": "Recife"} Espero ter ajudado.'))

    response = client.post("/extract", json={"texto": "incidente em Recife"})

    assert response.status_code == 200
    body = response.json()
    assert body["local"] == "Recife"
    assert body["tipo_incidente"] is None


def test_extract_with_unparseable_llm_output_returns_nulls(client):
    override_llm(FakeLLM("desculpe, não entendi"))

    response = client.post("/extract", json={"texto": "algum incidente"})

    assert response.status_code == 200
    assert response.json() == {
        "data_ocorrencia": None,
        "local": None,
        "tipo_incidente": None,
        "impacto": None,
    }


def test_extract_treats_null_strings_as_absent(client):
    override_llm(
        FakeLLM(
            '{"data_ocorrencia": "null", "local": "N/A",'
            ' "tipo_incidente": "lentidão", "impacto": ""}'
        )
    )

    response = client.post("/extract", json={"texto": "sistema lento"})

    assert response.status_code == 200
    assert response.json() == {
        "data_ocorrencia": None,
        "local": None,
        "tipo_incidente": "lentidão",
        "impacto": None,
    }


def test_extract_returns_503_when_llm_down(client):
    override_llm(DownLLM())

    response = client.post("/extract", json={"texto": "algum incidente"})

    assert response.status_code == 503


def test_extract_rejects_empty_text(client):
    response = client.post("/extract", json={"texto": ""})

    assert response.status_code == 422
