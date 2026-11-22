# -*- coding: utf-8 -*-
"""RAG Drivers — v10.

The Digital Twin owns driver selection, ranking, direction and strength.
The LLM interprets the authoritative driver report using the modular task prompt.
A deterministic fallback is used when the generated interpretation fails validation.
"""

import re

from knowledge.rag_pipeline import generate_answer
from utils.feature_semantics import build_semantic_context
from utils.prompt_builder import (
    load_base_prompt,
    load_model_prompt,
    load_style_prompt,
    load_task_prompt,
)

DEBUG = True

print("[RAG-DRIVERS MODULE]", __file__)
def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# PROMPT
# ======================================================


# ======================================================
# OUTPUT VALIDATION
# ======================================================


def is_valid(text):
    if not text or len(str(text).strip()) < 25:
        return False
    if "interpretation not available" in str(text).lower():
        return False
    return True


def _normalise_for_match(text):
    """Normalise prose for stable phrase checks."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


# Explicit aliases derived from the CSV feature names and descriptions.
# Keep aliases conservative: similar concepts are not necessarily the same feature.
FEATURE_ALIASES = {
    "density change in land imperviousness": [
        "land imperviousness change",
        "change in land imperviousness",
        "changes in land imperviousness",
        "imperviousness density change",
        "change in imperviousness density",
        "impervious surface change",
        "change in impervious surfaces",
        "land sealing change",
        "change in land sealing",
        "sealing density change",
    ],
    "density of tree cover": [
        "current tree cover density",
        "existing tree cover density",
        "density of tree canopy",
        "tree canopy density",
        "tree cover density",
    ],
    "change in tree cover density in the past decade": [
        "tree cover density change",
        "change in tree cover density",
        "past tree cover changes",
        "changes in tree cover density",
        "tree canopy density change",
        "change in tree canopy density",
        "tree cover change over the past decade",
        "decadal tree cover change",
        "tree cover loss or gain",
    ],
    "presence of grassland": [
        "grassland presence",
        "presence of grasslands",
        "current grassland cover",
        "grassland occurrence",
        "grassland areas",
    ],
    "change in grassland presence in the past decade": [
        "grassland presence change",
        "changes in grassland presence",
        "grassland cover change",
        "changes in grassland cover",
        "grassland gain or loss",
        "grassland loss",
        "loss of grassland",
        "grassland gain",
        "gain in grassland",
        "decadal grassland change",
        "grassland change over the past decade",
    ],
    "land use and cover": [
        "current land use and cover",
        "current land cover",
        "land cover classes",
        "land use classes",
        "land use categories",
        "land cover categories",
        "land use characteristics",
    ],
    "index of total productivity by plant phenology": [
        "vegetation productivity",
        "plant productivity",
        "plant phenology productivity",
        "phenological productivity",
        "productivity by plant phenology",
        "growing season integral",
        "vegetation growth integral",
    ],
    "change in average temperature compared to a recent past": [
        "average temperature change",
        "change in average temperature",
        "changes in average temperature",
        "average temperature changes",
        "mean temperature change",
        "change in mean temperature",
        "temperature change relative to the reference period",
        "temperature change compared with the reference period",
        "shifts in average temperature",
        "average temperature shifts",
        "shifts in mean temperature",
        "mean temperature shifts",
        "temperature increases",
        "rising average temperatures",
        "increase in average temperature",
        "increases in average temperature",
    ],
    "relative change in the potential evapotranspiration compared to a recent past": [
        "potential evapotranspiration change",
        "change in potential evapotranspiration",
        "changes in potential evapotranspiration",
        "potential et change",
        "change in potential et",
        "relative change in potential evapotranspiration",
        "relative potential evapotranspiration change",
    ],
    "cumulative change in precipitation compared to a recent past": [
        "cumulative precipitation change",
        "cumulative changes in precipitation",
        "change in cumulative precipitation",
        "changes in cumulative precipitation",
        "cumulative precipitation changes",
        "precipitation change relative to the reference period",
        "precipitation change compared with the reference period",
    ],
    "number of species potentially living in the cell": [
        "species richness",
        "potential species richness",
        "potential animal species richness",
        "number of potentially present species",
        "number of species potentially present",
        "potential number of species",
        "species potentially present in the cell",
        "number of animal species",
    ],
    "change in land use and cover in the past decade": [
        "change in land use and cover over the past decade",
        "changes in land use and cover",
        "land use and cover changes",
        "land use changes over the past decade",
        "land cover changes over the past decade",
        "land use change",
        "land use changes",
        "land cover change",
        "land cover changes",
        "land use and land cover change",
        "land use and land cover changes",
        "land use modification",
        "land use modifications",
        "land cover modification",
        "land cover modifications",
        "land-use changes over the past decade",
    ],
}

# These guards prevent a current-state feature from being matched inside wording
# that explicitly describes a temporal change feature.
_ALIAS_PREFIX_GUARDS = {
    "density of tree cover": (
        r"(?:change|changes|loss|gain|increase|decrease)\s+(?:in|of)\s+$",
        r"(?:change|changes)\s+in\s+(?:tree\s+)?canopy\s+$",
    ),
    "presence of grassland": (
        r"(?:change|changes|loss|gain)\s+(?:in|of)\s+$",
    ),
    "land use and cover": (
        r"(?:change|changes|modification|modifications)\s+in\s+$",
    ),
}


def _compile_phrase_pattern(phrase):
    """Compile a phrase allowing punctuation/hyphens between its words."""
    tokens = re.findall(r"[a-z0-9]+", str(phrase).lower())
    if not tokens:
        return None
    return re.compile(
        r"\b" + r"[\W_]+".join(map(re.escape, tokens)) + r"\b",
        flags=re.IGNORECASE,
    )


def _find_feature_match(text, feature):
    """Find a canonical feature or one of its explicitly approved aliases."""
    if not text or not feature:
        return None

    canonical = _normalise_for_match(feature)
    candidates = [str(feature)] + FEATURE_ALIASES.get(canonical, [])
    guards = _ALIAS_PREFIX_GUARDS.get(canonical, ())

    # Prefer longer expressions, reducing accidental matches of short aliases.
    candidates = sorted(set(candidates), key=len, reverse=True)
    for candidate in candidates:
        pattern = _compile_phrase_pattern(candidate)
        if pattern is None:
            continue
        for match in pattern.finditer(str(text)):
            prefix = str(text)[max(0, match.start() - 45):match.start()].lower()
            if any(re.search(guard, prefix) for guard in guards):
                continue
            return match

    return None


def _claims_unreported_significance(text):
    """Catch unsupported judgements that associations are/aren't significant."""
    normalised = _normalise_for_match(text)
    patterns = (
        r"\bstatistically significant\b",
        r"\bsignificantly associated\b",
        r"\bsignificant association\b",
        r"\bsignificant correlation\b",
        r"\bnot significant\b",
        r"\bno other reported associations\b",
        r"\bno other associations\b",
        r"\bonly .* significant\b",
    )
    return any(re.search(pattern, normalised) for pattern in patterns)


# The drivers task prompt asks the LLM to interpret the reported associations.
# These checks allow association language but reject unsupported causal claims.
_CAUSAL_CLAIM_PATTERNS = (
    # Reject causal claims, but allow association language required by drivers.txt.
    r"\bcaus(?:e|es|ed|ing)\b",
    r"\blead(?:s|ing)? to\b",
    r"\bresult(?:s|ing)? in\b",
    r"\bcontribut(?:e|es|ed|ing) to\b",
    r"\bdrives?\b",
    r"\binfluenc(?:e|es|ed|ing)\b",
    r"\baffect(?:s|ed|ing)?\b",
    r"\bimpact(?:s|ed|ing)?\b",
    r"\bdue to\b",
    r"\bresponsible for\b",
    r"\bdetermines?\b",
    r"\bplays? a role in\b",
)


def validate_interpretation(text, target=None, drivers=None):
    """Return concrete validation issues instead of a silent boolean rejection."""
    issues = []
    if not is_valid(text):
        issues.append("empty_or_too_short")
        return issues

    normalised = _normalise_for_match(text)

    if _claims_unreported_significance(text):
        issues.append("unsupported_statistical_significance_claim")

    if re.search(r"\d", str(text)):
        issues.append("contains_unrequested_numeric_value")

    recommendation_patterns = (
        r"\brecommend(?:s|ed|ing)?\b",
        r"\brecommendation(?:s)?\b",
        r"\bprioriti[sz](?:e|es|ed|ing|ation)\b",
        r"\bshould\s+(?:be\s+)?(?:protected|preserved|conserved|managed|monitored|restored)\b",
        r"\bmust\s+(?:be\s+)?(?:protected|preserved|conserved|managed|monitored|restored)\b",
        r"\bneed(?:s)? to\s+(?:protect|preserve|conserve|manage|monitor|restore)\b",
        r"\bessential to\s+(?:protect|preserve|conserve|manage|monitor|restore)\b",
    )
    if any(re.search(pattern, normalised) for pattern in recommendation_patterns):
        issues.append("management_recommendation")

    causal_hits = [
        pattern for pattern in _CAUSAL_CLAIM_PATTERNS
        if re.search(pattern, normalised)
    ]
    if causal_hits:
        print(
            "[RAG-DRIVERS VALIDATION WARNING] "
            "Potentially causal wording detected:",
            causal_hits
        )

    # Every strong driver must be named and its reported direction preserved.
    strong_drivers = [
        d for d in (drivers or [])
        if str(d.get("strength", "")).strip().lower() == "strong"
    ]
    
    for driver in strong_drivers:
        feature = str(driver.get("feature", "")).strip()
        direction = str(driver.get("direction", "")).strip().lower()

        if not feature:
            continue

        feature_match = _find_feature_match(text, feature)

        if not feature_match:
            issues.append("missing_strong_driver:" + feature)
            continue


        # Check direction only in sentences that explicitly refer to
        # this same feature, using its canonical name or an approved alias.
        lowered = str(text).lower()
        pos = feature_match.start()
        end_pos = feature_match.end()

        if direction in ("positive", "negative"):
            direction_patterns = {
                "positive": r"\bpositive(?:ly)?\b|\bdirect(?:ly)?\b",
                "negative": r"\bnegative(?:ly)?\b|\binverse(?:ly)?\b",
            }

            pattern = direction_patterns[direction]

            feature_sentences = []

            for sentence_match in re.finditer(r"[^.!?\n]+", lowered):
                sentence = sentence_match.group(0).strip()

                if _find_feature_match(sentence, feature):
                    feature_sentences.append(sentence)

            direction_match = None
            matched_sentence = None

            for sentence in feature_sentences:
                candidate = re.search(pattern, sentence)

                if candidate:
                    direction_match = candidate
                    matched_sentence = sentence
                    break

            print("[RAG-DRIVERS DIRECTION DEBUG]")
            print("  Feature:", feature)
            print("  Matched phrase:", repr(feature_match.group(0)))
            print("  Reported direction:", repr(direction))
            print("  Feature sentences:", repr(feature_sentences))
            print("  Direction pattern:", pattern)
            print("  Matched sentence:", repr(matched_sentence))
            print(
                "  Direction match:",
                repr(direction_match.group(0)) if direction_match else None
            )

            if not direction_match:
                issues.append("direction_not_explicit_near_driver:" + feature)


        # Identify the sentence containing the matched feature.
        feature_sentence_start = max(
            lowered.rfind(".", 0, pos),
            lowered.rfind("!", 0, pos),
            lowered.rfind("?", 0, pos),
            lowered.rfind("\n", 0, pos),
        ) + 1

        # Catch an explicit strength label that contradicts the authoritative report.
        after_feature = lowered[end_pos:end_pos + 90]
        explicit_strength = re.search(
            r"\bstrength\s*:\s*(strong|moderate)\b", after_feature
        )
        reported_strength = str(driver.get("strength", "")).strip().lower()

        if explicit_strength and reported_strength in ("strong", "moderate"):
            if explicit_strength.group(1) != reported_strength:
                issues.append("reported_strength_mismatch_for_driver:" + feature)

        elif reported_strength == "moderate":
            before_feature = lowered[max(feature_sentence_start, pos - 140):pos]

            strong_association = re.search(
                r"\bstrong(?:ly)?\s+(?:(?:positive|negative)(?:ly)?\s+)?"
                r"(?:statistical\s+)?associat(?:ed|ion)\b",
                before_feature,
            )

            moderate_association = re.search(
                r"\bmoderate(?:ly)?\s+(?:(?:positive|negative)(?:ly)?\s+)?"
                r"(?:statistical\s+)?associat(?:ed|ion)\b",
                before_feature[-100:],
            )

            if strong_association and not moderate_association:
                issues.append("strength_overstated_for_driver:" + feature)


    # If strong associations have opposing signs, reject a single net increase/decrease
    # claim about the target: it would collapse distinct reported directions.
    strong_directions = {
        str(d.get("direction", "")).strip().lower()
        for d in strong_drivers
        if str(d.get("direction", "")).strip().lower() in ("positive", "negative")
    }
    if len(strong_directions) > 1 and target:
        target_pattern = re.escape(str(target.lower()))
        trend_pattern = (
            r"\b(?:increase|increased|increasing|rise|rising|growth|decrease|"
            r"decreased|decreasing|decline|declining|reduction|reduced)\b"
            r"(?:\s+\w+){0,5}\s+(?:in|of)\s+(?:the\s+)?" + target_pattern
        )
        if re.search(trend_pattern, str(text).lower()):
            issues.append("net_target_trend_inferred_from_mixed_direction_drivers")

    return issues


def is_safe_context(text, target=None, drivers=None):
    """Boolean wrapper retained for callers that only need pass/fail."""
    return not validate_interpretation(text, target=target, drivers=drivers)


# ======================================================
# DETERMINISTIC ASSOCIATION SUMMARY AND FALLBACK
# ======================================================


def _selected_associations_for_interpretation(drivers):
    """
    Return all reported associations for interpretation,
    preserving the original ranking and order.
    """
    return list(drivers or [])


def build_authoritative_association_summary(target, drivers):
    """Render directions/strength from Digital Twin data, never from the LLM."""
    selected = _selected_associations_for_interpretation(drivers)
    if not selected:
        return (
            f"The Digital Twin did not report environmental associations for {target}."
        )

    clauses = []
    for driver in selected:
        feature = str(driver.get("feature", "Unnamed variable"))
        direction = str(driver.get("direction", "unspecified")).strip().lower()
        strength = str(driver.get("strength", "reported")).strip().lower()

        if direction in ("positive", "negative"):
            description = f"a {strength} {direction} statistical association"
        else:
            description = f"a {strength} statistical association"

        clauses.append(f"{description} between {feature} and {target}")

    # One sentence keeps the interpretation compact while preserving the
    # report order and the direction of every included association.
    if len(clauses) == 1:
        return f"The Digital Twin reports {clauses[0]}."
    joined = "; ".join(clauses[:-1]) + "; and " + clauses[-1]
    return "The Digital Twin reports " + joined + "."


def build_context_fallback():
    """A conservative context statement used when the LLM crosses its scope."""
    return (
        "The supplied semantic notes provide ecological context for the reported "
        "variables, but do not by themselves establish a specific mechanism "
        "connecting these variables to the target. The retrieved material does "
        "not support a stronger mechanistic explanation; the reported directions "
        "should therefore be interpreted as statistical associations, not causal effects."
    )


def fallback_explanation(target, drivers):
    """Safe complete interpretation without relying on unvalidated LLM prose."""
    if not drivers:
        return (
            f"The Digital Twin did not report environmental associations for {target}. "
            "The supplied material does not establish a specific ecological explanation."
        )
    summary = build_authoritative_association_summary(target, drivers)
    return f"{summary} {build_context_fallback()}".strip()


# ======================================================
# CLEAN OUTPUT
# ======================================================


def clean_output(text):
    return re.sub(r"\s+", " ", str(text).strip())


# ======================================================
# DRIVERS REPORT
# ======================================================


def build_drivers_report(target, drivers):
    associations = "\n".join(
        f"{i}. {d['feature']}\n"
        f"   Direction: {d['direction']}\n"
        f"   Strength: {d['strength']}"
        for i, d in enumerate(drivers, start=1)
    )
    return f"""
============================================================
DIGITAL TWIN DRIVERS REPORT — AUTHORITATIVE
============================================================

TARGET VARIABLE:
{target}

PRIMARY ASSOCIATED VARIABLES (already ranked by the Digital Twin):
{associations}

"""


# ======================================================
# MAIN
# ======================================================


def generate_drivers_explanation(target, drivers, features=None):
    print("\n[RAG-DRIVERS v10] START")

    try:
        semantic_context = ""
        if features:
            semantic_context = build_semantic_context(features)
            print("\n[RAG] SEMANTIC CONTEXT")
            print(semantic_context)

        drivers_report = build_drivers_report(target, drivers)
        semantic_section = (
            "\n\nECOLOGICAL SEMANTIC DESCRIPTIONS:\n" + semantic_context
            if semantic_context else ""
        )

        # Load all modular prompt components, including the drivers task prompt.
        base_prompt = "\n\n".join(
            component for component in (
                load_base_prompt(),
                load_model_prompt(),
                load_style_prompt(),
                load_task_prompt("drivers"),
            ) if component
        )

        # Add the authoritative report and semantic descriptions as task context.
        prompt = (
            base_prompt
            + f"\n\n{drivers_report}{semantic_section}\n"
        )

        if DEBUG:
            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        print("    llm_prompt_length:", len(prompt))

        top_drivers = "; ".join(
            str(d.get("feature", "")) for d in drivers
        )
        rag_query = (
            "Massaciuccoli Lake basin scientific evidence on the ecological "
            "context of the target variable and the following environmental "
            f"variables: target={target}; drivers={top_drivers}. "
            "Relevant context may include wetland ecology, water availability, "
            "climate conditions, biodiversity, and land-use characteristics."
        )

        print("\n[RAG] Query:")
        print(rag_query)

        raw = generate_answer(
            question=rag_query,
            features=features,
            extra_prompt=prompt,
            prompt_question="",
            modular_prompt=True,
        )

        debug_print("\n[RAG-DRIVERS] Raw contextual output:")
        debug_print(raw)

        interpretation = clean_output(raw) if is_valid(raw) else ""
        validation_issues = validate_interpretation(
            interpretation, target=target, drivers=drivers
        )

        print("[RAG-DRIVERS VALIDATION]", validation_issues)
        print(
            "[RAG-DRIVERS TEMP MATCH]",
            _find_feature_match(
                interpretation,
                "change in average temperature compared to a recent past"
            )
        )
        
        if validation_issues:
            debug_print("[RAG-DRIVERS] Validation rejected interpretation:")
            for issue in validation_issues:
                debug_print("  -", issue)
            debug_print("[RAG-DRIVERS] Using deterministic fallback.")
            final_text = fallback_explanation(target, drivers)
        else:
            final_text = interpretation

        debug_print("\n[RAG-DRIVERS] Final output:")
        debug_print(final_text)
        return final_text

    except Exception as e:
        print("\n🔥 RAG-DRIVERS ERROR:")
        print(e)
        return fallback_explanation(target, drivers)

    finally:
        print("[RAG-DRIVERS] END\n")
