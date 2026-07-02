"""Text preprocessing pipeline applied before sending input to the LLM.

Each step is a pure function so it can be tested in isolation;
`preprocess` chains them in order.
"""

import unicodedata


def strip_control_chars(text: str) -> str:
    """Remove control characters (e.g. \\x00, \\x1b), keeping \\n and \\t."""
    return "".join(
        ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C"
    )


def normalize_unicode(text: str) -> str:
    """Normalize to NFC so visually identical characters compare equal."""
    return unicodedata.normalize("NFC", text)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace (including newlines) into single spaces."""
    return " ".join(text.split())


_PIPELINE = (strip_control_chars, normalize_unicode, collapse_whitespace)


def preprocess(text: str) -> str:
    for step in _PIPELINE:
        text = step(text)
    return text
