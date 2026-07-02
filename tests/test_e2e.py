"""End-to-end tests against the live stack (FastAPI + Ollama).

These hit a running server over HTTP, so they are excluded from the default
pytest run (see `addopts` in pyproject.toml). Run them with `make test-e2e`
after starting the API and Ollama.

The real model is nondeterministic, so assertions stay loose: every response
must honor the JSON contract, and per-text checks only pin down what a
reasonable model reliably gets right (e.g. the city name).
"""

import datetime
import os
import unicodedata

import httpx
import pytest

pytestmark = pytest.mark.e2e

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT_SECONDS = 180.0

EXPECTED_KEYS = {"data_ocorrencia", "local", "tipo_incidente", "impacto"}


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            client.get("/healthz")
        except httpx.HTTPError:
            pytest.skip(f"API not reachable at {BASE_URL}; start it before e2e runs")
        yield client


def normalize(text: str) -> str:
    """Casefold and strip accents, so 'Incêndio' and 'incendio' compare equal."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def contains(haystack: str, needle: str) -> bool:
    return normalize(needle) in normalize(haystack)


def extract(client: httpx.Client, texto: str) -> dict:
    response = client.post("/extract", json={"texto": texto})
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == EXPECTED_KEYS
    assert all(value is None or isinstance(value, str) for value in body.values())
    return body


def test_readme_example(client):
    body = extract(
        client,
        "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor "
        "principal que afetou o sistema de faturamento por 2 horas.",
    )
    assert contains(body["local"], "são paulo")
    # "Ontem às 14h" must resolve against today's date injected in the prompt.
    assert str(datetime.date.today().year) in body["data_ocorrencia"]
    assert body["tipo_incidente"] is not None
    assert body["impacto"] is not None


def test_explicit_date_and_city(client):
    body = extract(
        client,
        "Em 15/03/2026 às 09h30, detectamos um vazamento de dados no sistema "
        "de RH em Belo Horizonte, expondo informações de 200 funcionários.",
    )
    assert contains(body["local"], "belo horizonte")
    assert "15" in body["data_ocorrencia"]
    assert contains(body["tipo_incidente"], "vazamento")


def test_fire_incident(client):
    body = extract(
        client,
        "Na terça-feira, um incêndio no data center do Rio de Janeiro derrubou "
        "os serviços de e-mail por 6 horas.",
    )
    assert contains(body["local"], "rio")
    assert contains(body["tipo_incidente"], "incendio")
    assert body["impacto"] is not None


def test_power_outage(client):
    body = extract(
        client,
        "Hoje de manhã uma queda de energia na fábrica de Manaus parou a linha "
        "de produção por 45 minutos.",
    )
    assert contains(body["local"], "manaus")
    assert body["tipo_incidente"] is not None
    assert body["impacto"] is not None


def test_sparse_text_keeps_contract(client):
    # Too little information to pin down field values; the contract is the test.
    extract(client, "Um usuário reportou um problema.")
