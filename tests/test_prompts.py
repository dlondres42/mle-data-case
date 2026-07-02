import datetime

from app.services.prompts import build_extraction_prompt


def test_prompt_includes_text_and_reference_date():
    prompt = build_extraction_prompt(
        "falha no servidor", today=datetime.date(2026, 7, 2)
    )

    assert "falha no servidor" in prompt
    assert "2026-07-02" in prompt


def test_prompt_defaults_to_current_date():
    prompt = build_extraction_prompt("qualquer texto")

    assert datetime.date.today().isoformat() in prompt
