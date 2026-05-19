# -*- coding: utf-8 -*-

"""
Feature Parser v29
QUALITATIVE ADJECTIVE SUPPORT + DOUBLE COUNT FIX

✔ Quantitative parsing
✔ Range parsing
✔ Semantic parsing
✔ Qualitative perturbation metadata
✔ Adjective qualitative support
✔ Prevents semantic double counting
✔ Backward compatible
"""

import re


# ======================================================
# FEATURE MAP
# ======================================================

FEATURE_MAP = {
    "temperature": "Change in average temperature compared to a recent past",

    "temperature change": "Change in average temperature compared to a recent past",

    "precipitation": "Cumulative change in precipitation compared to a recent past",

    "precipitation change": "Cumulative change in precipitation compared to a recent past",

    "biodiversity": "Number of species potentially living in the cell",

    "species richness": "Number of species potentially living in the cell",

    "tree cover": "Density of tree cover",

    "grassland": "Presence of grassland",

    "evapotranspiration": "Relative change in the potential evapotranspiration compared to a recent past"
}


# ======================================================
# SEMANTIC MAP
# ======================================================

SEMANTIC_MAP = {
    "warmer": ("temperature", 1.0),
    "hotter": ("temperature", 1.0),
    "cooler": ("temperature", -1.0),

    "drier": ("precipitation", -1.0),
    "dryer": ("precipitation", -1.0),
    "wetter": ("precipitation", 1.0),

    "more biodiversity": ("biodiversity", 10.0),
    "less biodiversity": ("biodiversity", -10.0),
}


# ======================================================
# QUALITATIVE ADJECTIVES
# ======================================================

QUALITATIVE_ADJECTIVE_MAP = {
    "warmer": {
        "feature": "Change in average temperature compared to a recent past",
        "direction": "increase"
    },

    "hotter": {
        "feature": "Change in average temperature compared to a recent past",
        "direction": "increase"
    },

    "cooler": {
        "feature": "Change in average temperature compared to a recent past",
        "direction": "decrease"
    },

    "drier": {
        "feature": "Cumulative change in precipitation compared to a recent past",
        "direction": "decrease"
    },

    "dryer": {
        "feature": "Cumulative change in precipitation compared to a recent past",
        "direction": "decrease"
    },

    "wetter": {
        "feature": "Cumulative change in precipitation compared to a recent past",
        "direction": "increase"
    }
}


# ======================================================
# BASELINE
# ======================================================

def build_default_features():

    return {
        'Density change in land imperviousness': 0,
        'Density of tree cover': 50,
        'Index of total productivity by plant phenology': 200,
        'Change in average temperature compared to a recent past': 0,
        'Relative change in the potential evapotranspiration compared to a recent past': 0,
        'Cumulative change in precipitation compared to a recent past': 0,
        'Number of species potentially living in the cell': 200,
        'Presence of grassland': 1,
    }


# ======================================================
# DYNAMIC FEATURE REGEX
# ======================================================

FEATURE_REGEX = "|".join(
    sorted(
        [re.escape(k) for k in FEATURE_MAP.keys()],
        key=len,
        reverse=True
    )
)


# ======================================================
# INTERNAL HELPERS
# ======================================================

def _apply_delta(features, modified, explicit, var_name, delta):

    mapped = FEATURE_MAP.get(var_name)

    if not mapped:
        return

    features[mapped] += delta

    modified.add(mapped)

    explicit.add(mapped)


def _apply_assignment(features, modified, explicit, var_name, value):

    mapped = FEATURE_MAP.get(var_name)

    if not mapped:
        return

    features[mapped] = value

    modified.add(mapped)

    explicit.add(mapped)


# ======================================================
# MAIN PARSER
# ======================================================

def parse_features(question: str, return_metadata=False):

    q = question.lower()

    features = build_default_features()

    modified_features = set()

    # 🔥 NEW
    explicitly_modified = set()

    assigned_variables = set()

    qualitative_changes = []

    # ==================================================
    # RANGE METADATA
    # ==================================================

    range_detected = False
    range_feature = None
    range_start = None
    range_end = None

    # ==================================================
    # NUMERIC DELTA
    # ==================================================

    numeric_pattern = rf"""
    ({FEATURE_REGEX})
    \s+
    (increases|decreases)
    \s+by\s+
    ([+\-]?\d+\.?\d*)
    """

    numeric_matches = re.findall(
        numeric_pattern,
        q,
        flags=re.VERBOSE
    )

    for var, direction, value in numeric_matches:

        value = float(value)

        if direction == "decreases":
            value = -value

        _apply_delta(
            features,
            modified_features,
            explicitly_modified,
            var,
            value
        )

    # ==================================================
    # SEMANTIC DELTA
    # ==================================================

    semantic_delta_pattern = rf"""
    ({FEATURE_REGEX})
    \s+
    (increase|decrease)
    \s+of\s+
    ([+\-]?\d+\.?\d*)
    """

    semantic_delta_matches = re.findall(
        semantic_delta_pattern,
        q,
        flags=re.VERBOSE
    )

    for var, direction, value in semantic_delta_matches:

        value = float(value)

        if direction == "decrease":
            value = -value

        _apply_delta(
            features,
            modified_features,
            explicitly_modified,
            var,
            value
        )

    # ==================================================
    # ASSIGNMENT
    # ==================================================

    assignment_pattern = rf"""
    ({FEATURE_REGEX})
    \s*
    (?:=|:)
    \s*
    ([+\-]?\d+\.?\d*)
    """

    assignment_matches = re.findall(
        assignment_pattern,
        q,
        flags=re.VERBOSE
    )

    for var, value in assignment_matches:

        value = float(value)

        _apply_assignment(
            features,
            modified_features,
            explicitly_modified,
            var,
            value
        )

        assigned_variables.add(var)

    # ==================================================
    # SEMANTIC ASSIGNMENT
    # ==================================================

    semantic_assignment_pattern = rf"""
    ({FEATURE_REGEX})
    \s+
    (?:equal\s+to|equals|is)
    \s+
    ([+\-]?\d+\.?\d*)
    """

    semantic_assignment_matches = re.findall(
        semantic_assignment_pattern,
        q,
        flags=re.VERBOSE
    )

    for var, value in semantic_assignment_matches:

        value = float(value)

        _apply_assignment(
            features,
            modified_features,
            explicitly_modified,
            var,
            value
        )

        assigned_variables.add(var)

    # ==================================================
    # COMPACT DELTA
    # ==================================================

    compact_pattern = rf"""
    ({FEATURE_REGEX})
    \s*
    ([+\-]\s*\d+\.?\d*)
    """

    compact_matches = re.findall(
        compact_pattern,
        q,
        flags=re.VERBOSE
    )

    for var, value in compact_matches:

        if var in assigned_variables:
            continue

        value = float(value.replace(" ", ""))
        mapped = FEATURE_MAP.get(var)

        if mapped in explicitly_modified:
            continue
        
        _apply_delta(
            features,
            modified_features,
            explicitly_modified,
            var,
            value
        )

    # ==================================================
    # RANGE PATTERN
    # ==================================================

    range_patterns = [

        rf"""
        ({FEATURE_REGEX})
        .*?
        from
        \s+
        ([+\-]?\d+\.?\d*)
        .*?
        to
        \s+
        ([+\-]?\d+\.?\d*)
        """,

        rf"""
        from
        \s+
        ([+\-]?\d+\.?\d*)
        .*?
        to
        \s+
        ([+\-]?\d+\.?\d*)
        .*?
        ({FEATURE_REGEX})
        """
    ]

    for pattern in range_patterns:

        match = re.search(
            pattern,
            q,
            flags=re.VERBOSE
        )

        if match:

            groups = match.groups()

            if groups[0] in FEATURE_MAP:

                var = groups[0]
                start = float(groups[1])
                end = float(groups[2])

            else:

                start = float(groups[0])
                end = float(groups[1])
                var = groups[2]

            range_detected = True

            range_feature = FEATURE_MAP.get(var)

            range_start = start
            range_end = end

            modified_features.add(range_feature)

            explicitly_modified.add(range_feature)

            break

    # ==================================================
    # QUALITATIVE VERBAL PATTERNS
    # ==================================================

    qualitative_pattern = rf"""
    ({FEATURE_REGEX})
    .*?
    (increase|decrease|increases|decreases)
    .*?
    (slightly|moderately|significantly|strongly|severely|extremely)
    """

    qualitative_matches = re.findall(
        qualitative_pattern,
        q,
        flags=re.VERBOSE
    )

    for var, direction, magnitude in qualitative_matches:

        feature = FEATURE_MAP.get(var)

        qualitative_changes.append({
            "feature": feature,
            "direction": direction,
            "magnitude": magnitude
        })

        modified_features.add(feature)

        explicitly_modified.add(feature)

    # ==================================================
    # QUALITATIVE ADJECTIVE PATTERNS
    # ==================================================

    adjective_pattern = r"""
    (slightly|moderately|significantly|strongly|severely|extremely)
    \s+
    (warmer|hotter|cooler|drier|dryer|wetter)
    """

    adjective_matches = re.findall(
        adjective_pattern,
        q,
        flags=re.VERBOSE
    )

    for magnitude, adjective in adjective_matches:

        semantic = QUALITATIVE_ADJECTIVE_MAP.get(adjective)

        if not semantic:
            continue

        qualitative_changes.append({
            "feature": semantic["feature"],
            "direction": semantic["direction"],
            "magnitude": magnitude
        })

        modified_features.add(semantic["feature"])

        explicitly_modified.add(semantic["feature"])

    # ==================================================
    # SEMANTIC WORDS (fallback only)
    # ==================================================

    for word, (var, delta) in SEMANTIC_MAP.items():

        if word not in q:
            continue

        mapped = FEATURE_MAP.get(var)

        # 🔥 prevent double counting
        if mapped in explicitly_modified:
            continue

        _apply_delta(
            features,
            modified_features,
            explicitly_modified,
            var,
            delta
        )

    # ==================================================
    # SIMPLE FALLBACK
    # ==================================================

    for var in FEATURE_MAP:

        mapped = FEATURE_MAP[var]

        if f"{var} increases" in q:

            if mapped not in explicitly_modified:

                features[mapped] += 1.0

                modified_features.add(mapped)

        if f"{var} decreases" in q:

            if mapped not in explicitly_modified:

                features[mapped] -= 1.0

                modified_features.add(mapped)

    # ==================================================
    # METADATA
    # ==================================================

    scenario_detected = (
        len(modified_features) > 0
        or len(qualitative_changes) > 0
    )

    metadata = {
        "features": features,

        "scenario_detected": scenario_detected,

        "modified_features": list(modified_features),

        "num_modified_features": len(modified_features),

        "range_detected": range_detected,
        "range_feature": range_feature,
        "range_start": range_start,
        "range_end": range_end,

        "qualitative_changes": qualitative_changes
    }

    if return_metadata:
        return metadata

    return features