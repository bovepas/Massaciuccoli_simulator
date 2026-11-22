from extraction.dependency.schema import DependencyExtraction
from utils.feature_mapping import normalize_feature_name


ABSTRACT_TARGETS = {
    "water availability", "water level", "climate stress",
    "hydrological stress", "hydrology", "water",
    "ecosystem productivity", "ecosystem stability",
}

RISK_TARGET_ALIASES = {
    "risk", "risk score", "risk_score", "ecosystem risk",
    "ecological risk", "ecosystem_risk",
    "ecosystem risk classification according to a variational autoencoder "
    "with a later application of a multi k-means process",
}


def _normalize_driver(variable: str):
    if not variable:
        return None
    cleaned = variable.strip()
    feature = normalize_feature_name(cleaned)
    if isinstance(feature, list):
        return cleaned
    return feature or cleaned


def _normalize_target(variable: str, question: str = None):
    cleaned = (variable or "").strip()
    lowered = " ".join(cleaned.lower().replace("_", " ").split())

    # Preserve an explicitly requested, distinct abstract target.
    if lowered == "ecosystem stability":
        return "ecosystem stability"
    if lowered in ABSTRACT_TARGETS:
        return lowered

    # The generic lake/ecosystem target means the CSV's risk classification.
    if (not lowered and question and any(term in question.lower() for term in
            ("ecosystem", "lake", "environment", "ecological system"))):
        return "risk_score"
    if lowered in RISK_TARGET_ALIASES:
        return "risk_score"
    explicit_nonrisk_abstract = any(term in lowered for term in (
        "ecosystem stability", "ecosystem productivity", "biodiversity"
    ))
    if (any(term in lowered for term in (
            "lake ecosystem", "ecosystem health", "environment of massaciuccoli",
            "ecosystem risk", "ecological risk",
        )) or ("ecosystem" in lowered and not explicit_nonrisk_abstract)):
        return "risk_score"

    feature = normalize_feature_name(cleaned)
    if feature == "ecosystem_risk":
        return "risk_score"
    if isinstance(feature, list):
        # Preserve abstract concepts for task-level resolution.
        return cleaned
    return feature or (cleaned if cleaned else None)


def dependency_extraction_to_inputs(extraction: DependencyExtraction, question: str = None):
    if extraction is None:
        raise ValueError("Dependency extraction is None")
    if extraction.intent != "dependency_query":
        raise ValueError(f"Unexpected intent: {extraction.intent}")

    driver = _normalize_driver(extraction.driver)
    target = _normalize_target(extraction.target, question=question)

    if not driver:
        raise ValueError("No driver extracted")
    if not target:
        raise ValueError("No target extracted")

    return {"driver": driver, "target": target}
