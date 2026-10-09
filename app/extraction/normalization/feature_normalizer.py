from typing import Tuple

from router.embedding import get_embedding

from extraction.normalization.feature_catalog import (
    get_features,
    get_feature_weights,
    get_feature_disambiguation,
)


# Debug: set to True to display all feature scores.
SHOW_ALL_SCORES = True


def cosine_similarity(
    a: list[float],
    b: list[float],
) -> float:
    """
    Compute cosine similarity between two embeddings.
    """

    if not a or not b:
        return 0.0

    if len(a) != len(b):
        raise ValueError(
            "Embeddings must have the same dimensionality."
        )

    dot_product = sum(
        x * y for x, y in zip(a, b)
    )

    norm_a = sum(
        x * x for x in a
    ) ** 0.5

    norm_b = sum(
        x * x for x in b
    ) ** 0.5

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def _apply_domain_disambiguation(
    expression: str,
    best_feature: str,
    best_score: float,
) -> Tuple[str, float]:
    """
    Apply domain-specific disambiguation rules after
    the embedding-based ranking.

    The cosine similarity remains the primary mechanism.
    This second level resolves known semantic ambiguities,
    even when the cosine winner is a different feature.

    For land-use expressions:

    - generic/current land-use expressions default to
      "Land use and cover"
    - explicit historical/temporal expressions select
      "Change in land use and cover in the past decade"
    - explicit territorial transitions/conversions are
      interpreted as changes of the current land-use state
    - "change" alone is NOT considered a historical indicator
    """

    disambiguation_rules = get_feature_disambiguation()

    expression_lower = expression.lower()

    feature_weights = get_feature_weights()

    expression_embedding = get_embedding(
        expression
    )

    for (
        default_feature,
        historical_feature,
    ), rule in disambiguation_rules.items():

        # -------------------------------------------------
        # 1. Direct land-use / land-cover reference
        # -------------------------------------------------

        land_use_terms = (
            "land use",
            "land cover",
            "land use and land cover",
            "land use and cover",
        )

        has_land_use_reference = any(
            term in expression_lower
            for term in land_use_terms
        )

        # -------------------------------------------------
        # 2. Territorial transition detection
        #
        # A transition/conversion involving a territorial
        # category is treated as current land-use semantics.
        # -------------------------------------------------

        transition_keywords = rule.get(
            "transition_keywords",
            [],
        )

        transition_indicators = (
            "from",
            "to",
            "into",
            "toward",
            "towards",
            "conversion",
            "transition",
        )

        has_transition_indicator = any(
            keyword in expression_lower
            for keyword in transition_indicators
        )

        territorial_categories = (
            "rural",
            "naturalistic",
            "industrial",
            "commercial",
            "military",
            "agricultural",
            "agriculture",
        )

        has_territorial_category = any(
            keyword in expression_lower
            for keyword in territorial_categories
        )

        has_territorial_transition = (
            has_transition_indicator
            and has_territorial_category
        )

        # -------------------------------------------------
        # If the expression does not belong to the
        # land-use domain, leave the cosine result unchanged.
        # -------------------------------------------------

        if not (
            has_land_use_reference
            or has_territorial_transition
        ):
            continue

        # -------------------------------------------------
        # 3. Historical indicators
        #
        # "change", "changes" and "changed" are deliberately
        # excluded because they can describe a current-state
        # transition.
        # -------------------------------------------------

        historical_keywords = rule.get(
            "historical_keywords",
            [],
        )

        historical_indicators = [
            keyword
            for keyword in historical_keywords
            if keyword in expression_lower
            and keyword not in (
                "change",
                "changes",
                "changed",
            )
        ]

        has_historical_indicator = bool(
            historical_indicators
        )

        # -------------------------------------------------
        # 4. Historical land-use feature
        # -------------------------------------------------

        if has_historical_indicator:

            historical_embedding = get_embedding(
                historical_feature
            )

            historical_score = cosine_similarity(
                expression_embedding,
                historical_embedding,
            )

            historical_weight = feature_weights.get(
                historical_feature,
                1.0,
            )

            historical_weighted_score = (
                historical_score
                * historical_weight
            )

            return (
                historical_feature,
                historical_weighted_score,
            )

        # -------------------------------------------------
        # 5. Current land-use feature
        #
        # This is the default for:
        # - generic land-use expressions
        # - current land-use expressions
        # - territorial transitions/conversions
        # -------------------------------------------------

        default_embedding = get_embedding(
            default_feature
        )

        default_score = cosine_similarity(
            expression_embedding,
            default_embedding,
        )

        default_weight = feature_weights.get(
            default_feature,
            1.0,
        )

        default_weighted_score = (
            default_score
            * default_weight
        )

        return (
            default_feature,
            default_weighted_score,
        )

    # No domain-specific ambiguity detected.
    return best_feature, best_score

def normalize_feature(
    expression: str,
) -> Tuple[str, float]:
    """
    Normalize a natural-language feature expression against
    the canonical dataset features using weighted embedding
    similarity followed by domain-specific disambiguation.

    Returns:
        (best_matching_feature, weighted_similarity_score)
    """

    expression = expression.strip()

    if not expression:
        raise ValueError(
            "Feature expression cannot be empty."
        )

    features = get_features()
    feature_weights = get_feature_weights()

    expression_embedding = get_embedding(
        expression
    )

    best_feature = None
    best_score = -1.0

    scores = []

    for feature in features:

        feature_embedding = get_embedding(
            feature
        )

        cosine_score = cosine_similarity(
            expression_embedding,
            feature_embedding,
        )

        weight = feature_weights.get(
            feature,
            1.0,
        )

        weighted_score = (
            cosine_score * weight
        )

        scores.append(
            (
                feature,
                cosine_score,
                weight,
                weighted_score,
            )
        )

        if weighted_score > best_score:
            best_score = weighted_score
            best_feature = feature

    # ---------------------------------------------------------
    # SECOND LEVEL: DOMAIN DISAMBIGUATION
    # ---------------------------------------------------------

    selected_feature, selected_score = (
        _apply_domain_disambiguation(
            expression,
            best_feature,
            best_score,
        )
    )

    if SHOW_ALL_SCORES:
        print()
        print(
            f"[FEATURE NORMALIZER] Expression: {expression}"
        )
        print("-" * 90)

        for (
            feature,
            cosine_score,
            weight,
            weighted_score,
        ) in sorted(
            scores,
            key=lambda x: x[3],
            reverse=True,
        ):
            print(
                f"{feature}\n"
                f"  cosine={cosine_score:.6f} "
                f"weight={weight:.2f} "
                f"weighted={weighted_score:.6f}"
            )

        print("-" * 90)

        print(
            f"COSINE BEST: {best_feature} "
            f"(weighted={best_score:.6f})"
        )

        if selected_feature != best_feature:
            print(
                f"DOMAIN DISAMBIGUATION: "
                f"{selected_feature} "
                f"(weighted={selected_score:.6f})"
            )

        print(
            f"FINAL: {selected_feature} "
            f"(weighted={selected_score:.6f})"
        )

        print()

    return selected_feature, selected_score