# -*- coding: utf-8 -*-
"""Proof-of-concept formatter for Massaciuccoli Digital Twin task outputs.

Suggested location in the project: /app/output_formatter.py

This first version is deliberately non-invasive:
- it never edits the object returned by a task;
- it preserves every original field/value under ``raw_result``;
- it formats only explicitly registered metrics;
- it exposes a machine-readable ``formatted_values`` list that can be included
  in an LLM prompt or used by a later output renderer;
- it avoids guessing units for unknown fields.

Initial API
-----------
    formatted = format_result("delta", task_result)
    llm_context = build_llm_context(formatted)

This module has no third-party dependencies. It is a prototype, not yet wired
into the orchestrator or task handlers.
"""

from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass
from numbers import Real
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


FORMATTER_VERSION = "0.1.1"
SUPPORTED_STATUSES = {"success", "partial", "unsupported", "unavailable", "error"}


@dataclass(frozen=True)
class FieldRule:
    """Formatting and interpretation metadata for a known result field."""

    label: str
    decimals: int = 3
    unit: Optional[str] = None
    kind: str = "derived"
    multiplier: float = 1.0
    integer: bool = False
    note: Optional[str] = None


# Paths are relative to the task result. A '*' component matches one path
# component, including list indexes. Only explicitly listed paths are formatted.
# The labels/units are intentionally conservative: unknown fields remain raw.
FIELD_RULES: Dict[str, Dict[Tuple[str, ...], FieldRule]] = {
    "delta": {
        # Current task_delta returns these values inside result["data"].
        ("data", "score_from"): FieldRule("Risk score iniziale", kind="predicted"),
        ("data", "score_to"): FieldRule("Risk score finale", kind="predicted"),
        ("data", "risk_from"): FieldRule("Livello di rischio iniziale", kind="predicted"),
        ("data", "risk_to"): FieldRule("Livello di rischio finale", kind="predicted"),
        ("data", "delta"): FieldRule("Variazione del risk score", kind="derived", note="Differenza tra score finale e iniziale; il segno va mantenuto."),
        # Flat aliases are retained for backward-compatible unit tests.
        ("score_from",): FieldRule("Risk score iniziale", kind="predicted"),
        ("score_to",): FieldRule("Risk score finale", kind="predicted"),
        ("risk_from",): FieldRule("Rischio iniziale", kind="predicted"),
        ("risk_to",): FieldRule("Rischio finale", kind="predicted"),
        ("delta",): FieldRule("Variazione del risk score", kind="derived", note="Differenza tra score finale e iniziale; il segno va mantenuto."),
    },
    "assessment": {
        ("data", "baseline_risk"): FieldRule("Rischio nello scenario di riferimento", kind="predicted"),
        ("data", "scenario_risk"): FieldRule("Rischio nello scenario modificato", kind="predicted"),
        ("data", "risk_delta"): FieldRule("Variazione del risk score", kind="derived", note="Differenza tra scenario modificato e riferimento."),
        ("baseline_risk",): FieldRule("Rischio nello scenario di riferimento", kind="predicted"),
        ("scenario_risk",): FieldRule("Rischio nello scenario modificato", kind="predicted"),
        ("risk_delta",): FieldRule("Variazione del risk score", kind="derived", note="Differenza tra scenario modificato e riferimento."),
        ("data", "*", "impact"): FieldRule("Contributo di attribuzione", decimals=3, kind="attribution"),
        ("data", "*", "contribution"): FieldRule("Contributo di attribuzione", decimals=3, kind="attribution"),
    },
    "comparison": {
        ("data", "scenario_a", "risk"): FieldRule("Risk score scenario A", kind="predicted"),
        ("data", "scenario_b", "risk"): FieldRule("Risk score scenario B", kind="predicted"),
        ("data", "scenario_a", "delta_from_baseline"): FieldRule("Variazione scenario A rispetto al riferimento", kind="derived"),
        ("data", "scenario_b", "delta_from_baseline"): FieldRule("Variazione scenario B rispetto al riferimento", kind="derived"),
        ("risk_difference",): FieldRule("Differenza di rischio (B − A)", kind="derived", note="Un valore positivo indica B maggiore di A; uno negativo indica B minore di A."),
    },
    "dependency": {
        # Current task_dependency groups these fields under result["data"].
        ("data", "dependency_score"): FieldRule("Punteggio di dipendenza", decimals=3, kind="association"),
        ("data", "confidence"): FieldRule("Confidenza dichiarata dal task", decimals=3, kind="categorical_or_numeric"),
        ("dependency_score",): FieldRule("Punteggio di dipendenza", decimals=3, kind="association"),
        ("confidence",): FieldRule("Confidenza dichiarata dal task", decimals=3, kind="categorical_or_numeric"),
    },
    "drivers": {
        ("data", "drivers", "*", "correlation"): FieldRule("Correlazione di Pearson", decimals=3, kind="statistical_association", note="Un'associazione statistica non dimostra da sola causalità."),
        ("data", "drivers", "*", "abs_corr"): FieldRule("Valore assoluto della correlazione", decimals=3, kind="statistical_association"),
    },
    "importance": {
        ("data", "*"): FieldRule("Punteggio di importanza", decimals=3, kind="model_importance", note="La scala dipende dal metodo impiegato; non interpretare il punteggio come percentuale senza metadati espliciti."),
        ("group_scores", "*"): FieldRule("Punteggio di importanza del gruppo", decimals=3, kind="model_importance"),
        ("data", "group_scores", "*"): FieldRule("Punteggio di importanza del gruppo", decimals=3, kind="model_importance"),
    },
    "importance_compare": {
        ("data", "score_a"): FieldRule("Importanza del primo elemento", decimals=3, kind="model_importance"),
        ("data", "score_b"): FieldRule("Importanza del secondo elemento", decimals=3, kind="model_importance"),
        ("score_a",): FieldRule("Importanza del primo elemento", decimals=3, kind="model_importance"),
        ("score_b",): FieldRule("Importanza del secondo elemento", decimals=3, kind="model_importance"),
    },
    "enm": {
        # Current task_enm returns its metrics inside result["data"].
        ("data", "training_auc"): FieldRule("AUC di training", decimals=3, kind="model_metric"),
        ("data", "mean_suitability"): FieldRule("Suitability media", decimals=3, kind="model_estimate"),
        ("data", "max_suitability"): FieldRule("Suitability massima", decimals=3, kind="model_estimate"),
        ("data", "num_hotspots"): FieldRule("Numero di hotspot", decimals=0, kind="count", integer=True),
        ("data", "largest_hotspot_fraction"): FieldRule("Frazione del maggiore hotspot", decimals=1, unit="%", multiplier=100.0, kind="derived_fraction", note="La frazione viene mostrata come percentuale; il valore grezzo resta invariato."),
        ("data", "dominance_ratio"): FieldRule("Rapporto di dominanza", decimals=3, kind="ratio"),
        ("data", "pct_above_0_2T"): FieldRule("Area sopra la soglia 0.2T", decimals=1, unit="%", kind="percentage"),
        ("data", "pct_above_0_5T"): FieldRule("Area sopra la soglia 0.5T", decimals=1, unit="%", kind="percentage"),
        ("data", "pct_above_1_0T"): FieldRule("Area sopra la soglia 1.0T", decimals=1, unit="%", kind="percentage"),
        ("data", "pct_above_1_2T"): FieldRule("Area sopra la soglia 1.2T", decimals=1, unit="%", kind="percentage"),
        ("data", "comparison", "habitat_delta"): FieldRule("Variazione dell'habitat", decimals=3, kind="derived"),
        ("data", "comparison", "core_delta"): FieldRule("Variazione dell'area core", decimals=3, kind="derived"),
        ("data", "comparison", "hotspot_delta"): FieldRule("Variazione del numero di hotspot", decimals=0, kind="count", integer=True),
        # Flat aliases are retained for backward-compatible unit tests.
        ("training_auc",): FieldRule("AUC di training", decimals=3, kind="model_metric"),
        ("mean_suitability",): FieldRule("Suitability media", decimals=3, kind="model_estimate"),
        ("max_suitability",): FieldRule("Suitability massima", decimals=3, kind="model_estimate"),
        ("num_hotspots",): FieldRule("Numero di hotspot", decimals=0, kind="count", integer=True),
        ("largest_hotspot_fraction",): FieldRule("Frazione del maggiore hotspot", decimals=1, unit="%", multiplier=100.0, kind="derived_fraction", note="La frazione viene mostrata come percentuale; il valore grezzo resta invariato."),
        ("dominance_ratio",): FieldRule("Rapporto di dominanza", decimals=3, kind="ratio"),
        ("pct_above_0_2T",): FieldRule("Area sopra la soglia 0.2T", decimals=1, unit="%", kind="percentage"),
        ("pct_above_0_5T",): FieldRule("Area sopra la soglia 0.5T", decimals=1, unit="%", kind="percentage"),
        ("pct_above_1_0T",): FieldRule("Area sopra la soglia 1.0T", decimals=1, unit="%", kind="percentage"),
        ("pct_above_1_2T",): FieldRule("Area sopra la soglia 1.2T", decimals=1, unit="%", kind="percentage"),
        ("comparison", "habitat_delta"): FieldRule("Variazione dell'habitat", decimals=3, kind="derived"),
        ("comparison", "core_delta"): FieldRule("Variazione dell'area core", decimals=3, kind="derived"),
        ("comparison", "hotspot_delta"): FieldRule("Variazione del numero di hotspot", decimals=0, kind="count", integer=True),
    },
}


# These paths are not safely interpretable without knowing the variable's
# catalog metadata. For task=data, baseline values and category codes therefore
# remain untouched in this prototype.


def _native(value: Any) -> Any:
    """Convert common NumPy-like scalar/container values to JSON-safe values.

    This conversion is used only for the prompt/export representation. The
    original result object is separately preserved in ``raw_result``.
    """
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value

    # NumPy scalars commonly expose item(); NumPy arrays expose tolist().
    if hasattr(value, "item") and callable(value.item):
        try:
            return _native(value.item())
        except (ValueError, TypeError):
            pass
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return _native(value.tolist())
        except (ValueError, TypeError):
            pass

    if isinstance(value, Mapping):
        return {str(k): _native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_native(v) for v in value]
    if isinstance(value, Real):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    # Paths and other diagnostic objects are represented as strings rather
    # than causing JSON serialization to fail.
    return str(value)


def _walk(value: Any, path: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], Any]]:
    """Yield every leaf and its path, keeping list indexes as path components."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, path + (str(key),))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, path + (str(index),))
    else:
        yield path, value


def _path_matches(pattern: Sequence[str], path: Sequence[str]) -> bool:
    if len(pattern) != len(path):
        return False
    return all(p == "*" or p == actual for p, actual in zip(pattern, path))


def _rule_for(task_type: str, path: Tuple[str, ...]) -> Optional[FieldRule]:
    rules = FIELD_RULES.get(task_type, {})
    # Prefer the most specific path if a future schema introduces overlapping rules.
    matches = [
        (sum(part != "*" for part in pattern), rule)
        for pattern, rule in rules.items()
        if _path_matches(pattern, path)
    ]
    return max(matches, key=lambda item: item[0])[1] if matches else None


def _fmt_number(value: Any, rule: FieldRule) -> Optional[str]:
    if not isinstance(value, Real) or isinstance(value, bool):
        return None
    number = float(value)
    if not math.isfinite(number):
        return "non disponibile"
    shown = number * rule.multiplier
    if rule.integer:
        rendered = f"{shown:,.0f}".replace(",", " ")
    else:
        # Fixed decimal places preserve small non-zero values instead of
        # accidentally rendering them as zero due to coarse rounding.
        rendered = f"{shown:.{rule.decimals}f}"
    if rule.unit:
        rendered = f"{rendered} {rule.unit}"
    return rendered


def _get_path(root: Any, path: Sequence[str]) -> Any:
    current = root
    for component in path:
        if isinstance(current, Mapping):
            if component not in current:
                return None
            current = current[component]
        elif isinstance(current, (list, tuple)):
            try:
                current = current[int(component)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def _has_payload(value: Any) -> bool:
    """Safely test whether a value carries content, including NumPy arrays."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (Mapping, list, tuple, set)):
        return bool(value)
    return True


def _derive_result_status(task_type: str, result: Mapping[str, Any]) -> Tuple[str, str]:
    """Return (status, source), preferring explicit task metadata over inference."""
    explicit = result.get("status")
    if isinstance(explicit, str) and explicit.lower() in SUPPORTED_STATUSES:
        return explicit.lower(), "explicit_result_status"

    error = result.get("error")
    if error:
        return "error", "result_error_field"

    if result.get("partial") is True:
        return "partial", "result_partial_flag"

    # A dependency score of 0 with an explicit unsupported marker is NOT a
    # real zero-strength estimate. Do not generalize this rule to other tasks.
    if task_type == "dependency":
        data = result.get("data")
        strength = str(result.get("dependency_strength", "")).strip().lower()
        supported = result.get("supported")
        if isinstance(data, Mapping):
            nested_strength = str(data.get("dependency_strength", "")).strip().lower()
            if nested_strength:
                strength = nested_strength
            supported = data.get("supported", supported)
        if strength == "unsupported" or supported is False:
            return "unsupported", "dependency_support_marker"

    # The current ENM handler marks engine failures through meta.source.
    meta = result.get("meta")
    if isinstance(meta, Mapping) and str(meta.get("source", "")).lower().endswith("_error"):
        return "error", "task_meta_error_marker"

    if not result or not any(_has_payload(value) for value in result.values()):
        return "unavailable", "empty_result"

    return "success", "inferred_nonempty_result"


def _value_status(task_type: str, rule: FieldRule, result_status: str, path: Tuple[str, ...]) -> str:
    if result_status in {"error", "unavailable"}:
        return result_status
    if result_status == "unsupported":
        return "unsupported"
    if rule.kind in {"predicted", "model_estimate", "model_metric", "model_importance"}:
        return "estimated"
    if rule.kind in {"derived", "derived_fraction", "attribution", "count", "percentage", "ratio"}:
        return "derived"
    if rule.kind == "statistical_association":
        return "statistical_association"
    if rule.kind == "association":
        return "estimated"
    return "unspecified"


def format_result(
    task_type: str,
    result: Mapping[str, Any],
    *,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized, non-destructive view of a task result.

    Args:
        task_type: Router task id, e.g. ``delta`` or ``enm``.
        result: Original dictionary returned by a task handler.
        status: Optional explicit status override. Prefer task-provided status
            when available; otherwise this prototype applies conservative rules.

    Returns a common envelope with the untouched task result under
    ``raw_result`` and a ``formatted_values`` list for known numeric fields.
    The function intentionally does not rewrite the task's data/interpretation.
    """
    if not isinstance(result, Mapping):
        raise TypeError("result deve essere un mapping/dizionario")

    task = str(task_type or "unknown").strip().lower()
    status_code, status_source = _derive_result_status(task, result)
    if status is not None:
        if status not in SUPPORTED_STATUSES:
            raise ValueError(f"status non valido: {status!r}")
        status_code, status_source = status, "caller_override"

    metrics: List[Dict[str, Any]] = []
    display_values: Dict[str, str] = {}
    unsupported_dependency = task == "dependency" and status_code == "unsupported"

    for path, value in _walk(result):
        rule = _rule_for(task, path)
        if rule is None:
            continue

        # The ENM engine currently uses 999 as a sentinel for a single-hotspot
        # case. Do not display that sentinel as an ordinary ratio.
        if task == "enm" and path in {("dominance_ratio",), ("data", "dominance_ratio")} and value == 999:
            display_value = "non applicabile (un solo hotspot)"
            field_status = "not_applicable"
            note = "Valore sentinella del task ENM; non è un rapporto misurato pari a 999."
        elif unsupported_dependency and path in {("dependency_score",), ("data", "dependency_score")}:
            display_value = "non supportato"
            field_status = "unsupported"
            note = "Il task dichiara la relazione unsupported: lo 0.0 grezzo non va interpretato come intensità misurata nulla."
        else:
            display_value = _fmt_number(value, rule)
            if display_value is None:
                # Some fields such as confidence may be categorical; keep them
                # as text rather than forcing numeric formatting.
                display_value = str(value) if value is not None else "non disponibile"
            field_status = _value_status(task, rule, status_code, path)
            note = rule.note

        path_string = ".".join(path)
        metric = {
            "path": path_string,
            "label": rule.label,
            "raw_value": _native(value),
            "display_value": display_value,
            "unit": rule.unit,
            "kind": rule.kind,
            "status": field_status,
        }
        if note:
            metric["note"] = note
        metrics.append(metric)
        display_values[path_string] = display_value

    raw_copy = copy.deepcopy(dict(result))
    return {
        "formatter_version": FORMATTER_VERSION,
        "task": task,
        "status": {
            "code": status_code,
            "source": status_source,
        },
        "summary": _native(result.get("summary", "")),
        "formatted_values": metrics,
        "display_values_by_path": display_values,
        "raw_result": _native(raw_copy),
        "formatting_notes": [
            "I valori originali sono conservati in raw_result.",
            "Sono formattati soltanto i campi esplicitamente registrati per il task.",
            "I campi non riconosciuti non ricevono unità o significati inventati.",
        ],
    }


def build_llm_context(formatted_result: Mapping[str, Any]) -> Dict[str, Any]:
    """Build the prototype context to pass to the explanatory LLM.

    This function keeps the raw structured fields available for scientific
    context and adds a canonical display list. The shared prompt should tell
    the LLM to preserve the supplied display_value for each registered field.
    It deliberately removes any previous interpretation from raw_result to
    avoid feeding an already-generated narrative back as if it were evidence.
    """
    if not isinstance(formatted_result, Mapping):
        raise TypeError("formatted_result deve essere un mapping/dizionario")

    raw = copy.deepcopy(dict(formatted_result.get("raw_result", {})))
    if isinstance(raw, dict):
        raw.pop("interpretation", None)

    return {
        "task": formatted_result.get("task", "unknown"),
        "result_status": copy.deepcopy(formatted_result.get("status", {})),
        "summary": formatted_result.get("summary", ""),
        "structured_results": _native(raw),
        "canonical_formatted_values": copy.deepcopy(formatted_result.get("formatted_values", [])),
        "instructions": [
            "Usa i risultati strutturati come fonte quantitativa del task.",
            "Per ogni campo presente in canonical_formatted_values, riproduci display_value senza modificarne il valore o l'unità.",
            "Non interpretare uno zero come assenza di effetto quando lo status del campo è unsupported.",
            "Non trasformare associazioni statistiche in relazioni causali.",
            "Non attribuire unità a campi che non le riportano.",
        ],
    }


def dumps_llm_context(formatted_result: Mapping[str, Any], *, indent: int = 2) -> str:
    """Serialize ``build_llm_context`` as readable JSON for prompt injection."""
    return json.dumps(
        build_llm_context(formatted_result),
        ensure_ascii=False,
        indent=indent,
        allow_nan=False,
    )


def _self_test() -> None:
    """Regression checks using shapes returned by the real task handlers."""
    # Delta: actual task shape nests metrics in result["data"].
    delta = {
        "summary": "Change in ecosystem risk (range analysis)",
        "data": {"score_from": 0.4012, "score_to": 0.3978, "delta": -0.0034,
                 "risk_from": "moderate", "risk_to": "moderate"},
        "drivers": [],
        "interpretation": "old text",
    }
    delta_before = copy.deepcopy(delta)
    formatted_delta = format_result("delta", delta)
    assert delta == delta_before, "format_result deve lasciare invariato il risultato originale"
    displays = formatted_delta["display_values_by_path"]
    assert displays["data.delta"] == "-0.003"
    assert displays["data.score_from"] == "0.401"

    # Dependency: actual task shape puts unsupported marker and zero under data.
    dependency = {
        "summary": "Conceptual dependency analysis",
        "data": {"dependency_score": 0.0, "dependency_strength": "unsupported",
                 "interaction_type": "generic ecosystem interaction",
                 "confidence": "low", "direction": "unknown"},
        "drivers": [],
        "interpretation": "Some explanation",
    }
    formatted_dependency = format_result("dependency", dependency)
    score_metric = next(x for x in formatted_dependency["formatted_values"]
                        if x["path"] == "data.dependency_score")
    assert score_metric["raw_value"] == 0.0
    assert score_metric["display_value"] == "non supportato"
    assert formatted_dependency["status"]["code"] == "unsupported"

    # ENM: metrics in the current task_enm output are under result["data"].
    enm = {
        "type": "enm",
        "summary": "Species distribution model for example species",
        "data": {"mean_suitability": 0.52466, "pct_above_0_5T": 49.157,
                 "largest_hotspot_fraction": 0.326, "dominance_ratio": 999,
                 "num_hotspots": 1, "comparison": {"habitat_delta": 0.0,
                 "core_delta": 0.0, "hotspot_delta": 0}},
        "drivers": [],
        "interpretation": "example",
        "meta": {"source": "maxent_enm"},
    }
    formatted_enm = format_result("enm", enm)
    enm_displays = formatted_enm["display_values_by_path"]
    assert enm_displays["data.mean_suitability"] == "0.525"
    assert enm_displays["data.pct_above_0_5T"] == "49.2 %"
    assert enm_displays["data.largest_hotspot_fraction"] == "32.6 %"
    assert enm_displays["data.dominance_ratio"] == "non applicabile (un solo hotspot)"
    assert enm_displays["data.num_hotspots"] == "1"

    enm_error = {"type": "enm", "summary": "ENM analysis failed", "data": {},
                 "drivers": [], "interpretation": "failed", "meta": {"source": "enm_error"}}
    assert format_result("enm", enm_error)["status"]["code"] == "error"

    # Unknown fields and data-task baselines must not get guessed units or formatting.
    data = {"feature": "Land use and cover", "baseline": 2110.0}
    formatted_data = format_result("data", data)
    assert formatted_data["formatted_values"] == []
    assert formatted_data["raw_result"]["baseline"] == 2110.0

    # Context must be serializable and should not include a previous narrative.
    context_json = dumps_llm_context(formatted_delta)
    assert "old text" not in context_json
    json.loads(context_json)


def _demo() -> None:
    """Print representative examples in the same shape as real task results."""
    examples = {
        "delta": {
            "summary": "Change in ecosystem risk (range analysis)",
            "data": {"score_from": 0.4012, "score_to": 0.3978, "delta": -0.0034,
                     "risk_from": "moderate", "risk_to": "moderate"},
            "drivers": [], "interpretation": "example",
        },
        "dependency": {
            "summary": "Conceptual dependency analysis",
            "data": {"dependency_score": 0.0, "dependency_strength": "unsupported",
                     "interaction_type": "generic ecosystem interaction",
                     "confidence": "low", "direction": "unknown"},
            "drivers": [], "interpretation": "example",
        },
        "enm": {
            "type": "enm", "summary": "Species distribution model for example species",
            "data": {"mean_suitability": 0.52466, "pct_above_0_5T": 49.157,
                     "largest_hotspot_fraction": 0.326, "dominance_ratio": 999,
                     "num_hotspots": 1},
            "drivers": [], "interpretation": "example", "meta": {"source": "maxent_enm"},
        },
    }
    for task, result in examples.items():
        print(f"\n=== {task} ===")
        print(json.dumps(format_result(task, result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Proof-of-concept formatter del Massaciuccoli Digital Twin")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--self-test", action="store_true", help="Esegue i controlli interni")
    group.add_argument("--demo", action="store_true", help="Mostra esempi di formattazione")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("SELF-TEST OK")
    else:
        _demo()
