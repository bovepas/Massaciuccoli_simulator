from extraction.comparison.schema import ComparisonExtraction
from utils.feature_mapping import normalize_feature_name
from utils.scenario_parser import qualitative_to_delta


def _normalize_variable(variable):
    """
    Convert the semantic variable name returned by the extractor
    into the canonical dataset feature name.
    """

    feature = normalize_feature_name(variable)

    if feature:
        return feature

    return variable


def _normalize_qualitative_magnitude(magnitude):
    """
    Normalize natural-language qualitative magnitudes produced by
    the LLM into the canonical values expected by the legacy
    deterministic qualitative logic.
    """

    if magnitude is None:
        return "default"

    normalized = str(magnitude).strip().lower()

    mapping = {
        "slight": "slight",
        "slightly": "slight",

        "significant": "significant",
        "significantly": "significant",
        "substantial": "significant",
        "substantially": "significant",

        "extreme": "extreme",
        "extremely": "extreme",

        "default": "default",
    }

    return mapping.get(normalized, "default")


def _normalize_qualitative_direction(
    direction,
    original_expression=None,
    interpretation=None,
):
    """
    Normalize the direction of a qualitative modification.

    If the extractor leaves direction null, infer it only from the
    explicit semantic text already extracted by the LLM.
    """

    if direction in {
        "increase",
        "decrease",
        "change",
    }:
        return direction

    text = " ".join(
        x for x in [
            original_expression,
            interpretation,
        ]
        if x
    ).lower()

    decrease_terms = [
        "decrease",
        "decreases",
        "decreased",
        "decline",
        "declines",
        "declined",
        "lower",
        "lowers",
        "lowered",
        "reduce",
        "reduces",
        "reduced",
    ]

    increase_terms = [
        "increase",
        "increases",
        "increased",
        "rise",
        "rises",
        "rose",
        "higher",
        "raises",
        "raised",
    ]

    if any(term in text for term in decrease_terms):
        return "decrease"

    if any(term in text for term in increase_terms):
        return "increase"

    return "change"


def _modification_to_value(
    modification,
    feature_stats=None,
):
    """
    Convert one semantic comparison modification into the
    representation expected by task_comparison.

    Numeric interpretation and deterministic arithmetic remain
    in Python.
    """

    modification_type = modification.modification_type

    # --------------------------------------------------
    # DELTA
    # --------------------------------------------------

    if modification_type == "delta":

        if modification.value is None:
            raise ValueError(
                f"Delta modification without value: "
                f"{modification.original_expression}"
            )

        return modification.value

    # --------------------------------------------------
    # PERCENTAGE
    # --------------------------------------------------

    if modification_type == "percentage":

        if modification.value is None:
            raise ValueError(
                f"Percentage modification without value: "
                f"{modification.original_expression}"
            )

        value = float(modification.value)

        if modification.direction == "decrease":
            value = -abs(value)

        elif modification.direction == "increase":
            value = abs(value)

        return {
            "type": "percentage_change",
            "value": value,
        }

    # --------------------------------------------------
    # TARGET
    # --------------------------------------------------

    if modification_type == "target":

        if modification.value is None:
            raise ValueError(
                f"Target modification without value: "
                f"{modification.original_expression}"
            )

        return {
            "type": "target",
            "value": modification.value,
        }

    # --------------------------------------------------
    # QUALITATIVE
    # --------------------------------------------------

    if modification_type == "qualitative":

        if feature_stats is None:
            raise ValueError(
                "feature_stats is required for qualitative "
                "comparison modifications"
            )

        direction = _normalize_qualitative_direction(
            modification.direction,
            modification.original_expression,
            modification.interpretation,
        )

        magnitude = _normalize_qualitative_magnitude(
            modification.magnitude
        )

        return qualitative_to_delta(
            variable=modification.variable,
            direction=direction,
            magnitude=magnitude,
            feature_stats=feature_stats,
        )

    # --------------------------------------------------
    # STATE CHANGE
    # --------------------------------------------------

    if modification_type == "state_change":

        if modification.to_value is None:
            raise ValueError(
                f"State change without to_value: "
                f"{modification.original_expression}"
            )

        return modification.to_value

    raise ValueError(
        f"Unsupported comparison modification type: "
        f"{modification_type}"
    )


def _scenario_to_dict(
    modifications,
    feature_stats=None,
):
    """
    Convert a list of semantic modifications into a scenario dict.
    """

    scenario = {}

    for modification in modifications:

        feature = _normalize_variable(
            modification.variable
        )

        if not feature:
            raise ValueError(
                f"Could not normalize variable: "
                f"{modification.variable}"
            )

        value = _modification_to_value(
            modification,
            feature_stats=feature_stats,
        )

        scenario[feature] = value

    return scenario


def comparison_extraction_to_inputs(
    extraction: ComparisonExtraction,
    feature_stats=None,
):
    """
    Convert ComparisonExtraction into the two scenario dictionaries
    consumed by the comparison task.

    The extractor performs semantic interpretation.
    This bridge performs deterministic structural conversion
    and numerical interpretation.
    """

    if extraction is None:
        raise ValueError(
            "Comparison extraction is None"
        )

    if extraction.intent != "scenario_comparison":
        raise ValueError(
            f"Unsupported comparison intent: "
            f"{extraction.intent}"
        )

    scenario_a = _scenario_to_dict(
        extraction.scenario_a,
        feature_stats=feature_stats,
    )

    scenario_b = _scenario_to_dict(
        extraction.scenario_b,
        feature_stats=feature_stats,
    )

    if not scenario_a:
        raise ValueError(
            "Scenario A contains no usable modifications"
        )

    if not scenario_b:
        raise ValueError(
            "Scenario B contains no usable modifications"
        )

    return {
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
    }