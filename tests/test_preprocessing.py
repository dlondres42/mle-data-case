import pytest

from app.services.preprocessing import (
    collapse_whitespace,
    preprocess,
    strip_control_chars,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("hello world", "hello world"),
        ("hello   world", "hello world"),
        ("hello\nworld", "hello world"),
        ("  hello \t world \n", "hello world"),
        ("hello \x00world\x1b", "hello world"),
        ("", ""),
    ],
)
def test_preprocess(raw: str, expected: str):
    assert preprocess(raw) == expected


def test_strip_control_chars_keeps_newline_and_tab():
    assert strip_control_chars("a\x00b\nc\td") == "ab\nc\td"


def test_collapse_whitespace():
    assert collapse_whitespace("a  b\n\nc\t d") == "a b c d"


def test_preprocess_keeps_accents():
    assert preprocess("São Paulo às 14h") == "São Paulo às 14h"
