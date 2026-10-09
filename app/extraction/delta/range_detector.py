# -*- coding: utf-8 -*-
"""
Range detector — deterministic structural parser.

Responsibility:
    Detect whether the user's text explicitly contains a numerical
    start/end range.

It does NOT:
    - identify the feature/variable
    - interpret increase/decrease semantics
    - calculate the change
    - call the LLM

A range is returned only when TWO numerical endpoints are explicitly
present in a start/end construction.
"""

import re
from typing import Optional, Dict


# ------------------------------------------------------------------
# Basic lexical components
# ------------------------------------------------------------------

# Supports:
#   20
#   -20
#   +20
#   20.5
#   20,5
_NUMBER = r"[+-]?\d+(?:[.,]\d+)?"


# Supports:
#   %
#   °C
#   ° C
#
# The unit is intentionally optional.
# If it is absent, the semantic layer may deduce it later.
_UNIT = r"(?:°\s*C|%)?"


# Italian articles that may appear between the range connector
# and the numerical value:
#
#   tra il 20% e il 40%
#   tra la temperatura ...      (not directly relevant here, but
#                                harmless structurally)
#
# We only allow them where a number is expected.
_ARTICLE = r"(?:il|lo|la|i|gli|le)?"


# ------------------------------------------------------------------
# Range patterns
# ------------------------------------------------------------------

# Important:
# These patterns require BOTH numerical endpoints.
# We never invent 0 or any other missing endpoint.
#
# Supported structural forms include:
#
# Italian:
#   da 20 a 40
#   da 20% a 40%
#   dal 20 al 40%
#   dallo 20 allo 40
#   dalla 20 alla 40
#   dai 20 ai 40
#   dagli 20 agli 40
#   dalle 20 alle 40
#
#   tra 20 e 40
#   tra il 20 e il 40
#   tra il 20% e il 40%
#   fra 20 e 40
#   fra il 20% e il 40%
#
# English:
#   from 20 to 40
#   between 20 and 40
#   between 20% and 40%
#
_RANGE_PATTERNS = [

    # --------------------------------------------------------------
    # da X a Y / dal X al Y / ... / from X to Y
    # --------------------------------------------------------------
    re.compile(
        rf"""
        \b
        (?:
            da
            |
            dal
            |
            dallo
            |
            dalla
            |
            dai
            |
            dagli
            |
            dalle
            |
            from
        )
        \s+
        {_ARTICLE}
        \s*
        ({_NUMBER})
        \s*
        ({_UNIT})
        \s*
        (?:
            a
            |
            al
            |
            allo
            |
            alla
            |
            ai
            |
            agli
            |
            alle
            |
            to
        )
        \s+
        {_ARTICLE}
        \s*
        ({_NUMBER})
        \s*
        ({_UNIT})
        """,
        re.IGNORECASE | re.VERBOSE,
    ),

    # --------------------------------------------------------------
    # tra X e Y / fra X e Y / between X and Y
    # --------------------------------------------------------------
    re.compile(
        rf"""
        \b
        (?:
            tra
            |
            fra
            |
            between
        )
        \s+
        {_ARTICLE}
        \s*
        ({_NUMBER})
        \s*
        ({_UNIT})
        \s*
        (?:
            e
            |
            and
        )
        \s+
        {_ARTICLE}
        \s*
        ({_NUMBER})
        \s*
        ({_UNIT})
        """,
        re.IGNORECASE | re.VERBOSE,
    ),
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_float(value: str) -> float:
    """Convert Italian or English decimal notation to float."""
    return float(value.replace(",", "."))


def _normalize_unit(unit: str) -> Optional[str]:
    """
    Normalize textual units to the canonical schema units.

    Returns:
        "degC"
        "percent"
        None
    """
    if not unit:
        return None

    unit = unit.lower().replace(" ", "")

    if unit == "°c":
        return "degC"

    if unit == "%":
        return "percent"

    return None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def detect_range(text: str) -> Optional[Dict]:
    """
    Return explicit range metadata or None.

    Returned structure:

        {
            "from_value": 20.0,
            "to_value": 40.0,
            "unit": "percent",
            "matched_text": "tra il 20% e il 40%"
        }

    If no explicit two-endpoint range exists:
        None

    The detector is deliberately structural:
    it does not infer the variable or its semantic unit.
    """

    if not text:
        return None

    for pattern in _RANGE_PATTERNS:
        match = pattern.search(text)

        if not match:
            continue

        # Every pattern has the same four semantic captures:
        #
        #   from value
        #   from unit
        #   to value
        #   to unit
        #
        from_raw, from_unit, to_raw, to_unit = match.groups()

        from_value = _to_float(from_raw)
        to_value = _to_float(to_raw)

        unit_from = _normalize_unit(from_unit)
        unit_to = _normalize_unit(to_unit)

        # If only one endpoint carries the unit,
        # use that unit for the complete range.
        unit = unit_from or unit_to

        # If both endpoints carry units, they must agree.
        if unit_from and unit_to and unit_from != unit_to:
            return None

        return {
            "from_value": from_value,
            "to_value": to_value,
            "unit": unit,
            "matched_text": match.group(0).strip(),
        }

    return None