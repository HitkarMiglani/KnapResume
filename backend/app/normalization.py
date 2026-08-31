import unicodedata

MAX_BULLET_LENGTH = 500

_BULLET_MARKERS = ("- ", "* ", "• ")


class NormalizationError(ValueError):
    pass


def normalize_fact(raw_text: str) -> str:
    """Deterministically normalize a raw source fact into an atomic bullet.

    Rules (ADR 0002): NFC normalization, outer whitespace trim, strip one leading
    bullet marker, collapse horizontal whitespace, reject empty/multiline input,
    enforce a maximum length.
    """
    text = unicodedata.normalize("NFC", raw_text).strip()

    for marker in _BULLET_MARKERS:
        if text.startswith(marker):
            text = text[len(marker) :].strip()
            break

    if "\n" in text or "\r" in text:
        raise NormalizationError("source fact must be a single line")

    text = " ".join(text.split())

    if not text:
        raise NormalizationError("source fact must not be empty")

    if len(text) > MAX_BULLET_LENGTH:
        raise NormalizationError(f"source fact exceeds {MAX_BULLET_LENGTH} characters")

    return text
