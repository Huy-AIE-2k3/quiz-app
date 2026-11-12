"""Question Utilities for Math & Physics Number Parsing and Stable Shuffling."""

import hashlib
import re
import unicodedata
import uuid
from decimal import Decimal
from typing import Any


def normalize_nfc(text: str) -> str:
    """Normalizes text to Unicode NFC (canonical decomposition + composition)."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


_FRACTION_REGEX = re.compile(r"^[+-]?\s*\d+\s*/\s*[+-]?\s*\d+$")


def parse_number(val: Any) -> float:
    """Parses a numerical string, integer, float, or fraction into a standard float.

    Supports:
    - Standard integers and floats: '42', '-3.14', '0.005'
    - Scientific notation: '1e-3', '3.14e2', '-2.5E-4'
    - Fractions: '1/2', '-3/4', '7 / 3'
    - Comma decimal separators: '3,14' -> 3.14

    Raises ValueError if input cannot be parsed or represents inf/nan.
    """
    if val is None:
        raise ValueError("Giá trị số không được rỗng.")

    if isinstance(val, (int, float, Decimal)):
        fval = float(val)
        if fval != fval or fval in (float("inf"), float("-inf")):
            raise ValueError("Không hỗ trợ giá trị vô cùng (inf) hoặc NaN.")
        return fval

    s = str(val).strip()
    if not s:
        raise ValueError("Chuỗi số không được rỗng.")

    # Check for fraction notation: e.g. "1/2", "-3/4"
    if "/" in s and _FRACTION_REGEX.match(s):
        try:
            parts = s.split("/")
            num = float(parts[0].strip())
            den = float(parts[1].strip())
            if den == 0:
                raise ValueError("Mẫu số không thể bằng 0.")
            res = num / den
            if res != res or res in (float("inf"), float("-inf")):
                raise ValueError("Không hỗ trợ giá trị vô cùng (inf) hoặc NaN.")
            return res
        except (ValueError, ZeroDivisionError) as err:
            raise ValueError(f"Không thể phân tích phân số: {s}") from err

    # Replace comma with dot if comma is used as decimal separator
    if "," in s and "." not in s:
        s = s.replace(",", ".")

    try:
        res = float(s)
        if res != res or res in (float("inf"), float("-inf")):
            raise ValueError("Không hỗ trợ giá trị vô cùng (inf) hoặc NaN.")
        return res
    except ValueError as err:
        raise ValueError(f"Không thể phân tích giá trị số: '{val}'") from err


def stable_key(seed: int | None, qid: str | uuid.UUID, oid: str) -> str:
    """Generates a deterministic sorting key for options shuffling.

    Given identical seed, question id, and option id, produces identical hash key.
    Given different seeds, produces different uniform ordering.
    If seed is None, returns original oid (unshuffled order).
    """
    if seed is None:
        return str(oid)
    raw = f"{seed}:{str(qid)}:{str(oid)}".encode()
    return hashlib.sha256(raw).hexdigest()
