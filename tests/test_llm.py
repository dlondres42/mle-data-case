import json

import httpx
import pytest

from app.services.llm import LLMUnavailableError, OllamaClient


def make_client(handler, **kwargs) -> OllamaClient:
    """Build an OllamaClient whose HTTP calls are answered by `handler`."""
    transport = httpx.MockTransport(handler)
    return OllamaClient(
        base_url="http://testserver",
        model="test-model",
        client=httpx.Client(transport=transport),
        **kwargs,
    )


def test_generate_returns_response_text():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": '{"local": "São Paulo"}'})

    client = make_client(handler)

    assert client.generate("any prompt") == '{"local": "São Paulo"}'


def test_generate_sends_model_prompt_and_json_format():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": "{}"})

    make_client(handler).generate("meu prompt")

    assert captured["url"] == "http://testserver/api/generate"
    assert captured["body"] == {
        "model": "test-model",
        "prompt": "meu prompt",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }


def test_generate_sends_schema_as_format_when_given():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"response": "{}"})

    schema = {"type": "object", "properties": {"local": {"type": "string"}}}
    make_client(handler, format_schema=schema).generate("meu prompt")

    assert captured["body"]["format"] == schema


def test_generate_raises_when_server_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(LLMUnavailableError):
        make_client(handler).generate("any prompt")


def test_generate_raises_on_http_error_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "model not found"})

    with pytest.raises(LLMUnavailableError):
        make_client(handler).generate("any prompt")
