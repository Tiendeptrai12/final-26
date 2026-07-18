"""Vietnamese Correction model wrapper (Seq2Seq).

Serves as the text normalizer/corrector for query preprocessing and indexing.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None
_load_failed = False


def _load_model() -> None:
    global _tokenizer, _model, _load_failed
    if _model is not None or _load_failed:
        return

    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        model_name = "bmd1905/vietnamese-correction-v2"
        logger.info(f"Loading Vietnamese correction model '{model_name}'...")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        logger.info("Vietnamese correction model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Vietnamese correction model: {e}")
        _load_failed = True


def correct_text(text: str) -> str:
    """Correct Vietnamese spelling and diacritics of the input text.

    If the model fails to load or execute, it gracefully returns the original text.
    """
    if not text or not text.strip():
        return text

    _load_model()
    if _model is None or _load_failed:
        return text

    try:
        # Use CPU explicitly to avoid device mismatched issues
        inputs = _tokenizer(text, return_tensors="pt")
        outputs = _model.generate(**inputs, max_length=256)
        corrected = _tokenizer.decode(outputs[0], skip_special_tokens=True)
        return corrected.strip()
    except Exception as e:
        logger.error(f"Failed to run Vietnamese correction on text '{text}': {e}")
        return text
