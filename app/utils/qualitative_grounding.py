"""
Shared qualitative-change grounding for the Massaciuccoli Digital Twin.
"""

import math

from versions.v6_1_emulator import NUM_FEATURES
from utils.model_input_builder import compute_baseline, compute_feature_statistics


QUALITATIVE_SCALE = {
    "slightly": 0.25,
    "moderately": 0.50,
    "significantly": 1.00,
    "substantially": 1.50,
    "strongly": 2.00,
    "severely": 2.50,
    "extremely": 3.00,
}

QUALITATIVE_EXCLUDED_FEATURES = {
    "Density change in land imperviousness",
}

FEATURE_BOUNDS = {
    "Density of tree cover": (0.0, 100.0),
    "Index of total productivity by plant phenology": (0.0, None),
    "Number of species potentially living in the cell": (0.0, None),
}

_DIRECTION_SIGN = {
    "increase": 1.0, "increases": 1.0, "increasing": 1.0, "increased": 1.0,
    "gain": 1.0,
    "decrease": -1.0, "decreases": -1.0, "decreasing": -1.0,
    "decreased": -1.0, "loss": -1.0,
}


def ground_qualitative_changes(features, qualitative_changes, dataset):
    """
    Return (grounded_features, qualitative_modifications).

    grounded_features contains absolute final values for reporting.
    qualitative_modifications contains structured absolute deltas for
    build_input_df(..., interpret_percentages=True).
    """
    grounded = dict(features or {})
    modifications = {}

    if not qualitative_changes:
        return grounded, modifications

    if dataset is None:
        raise ValueError("Dataset is required for qualitative grounding.")

    baseline = compute_baseline(dataset)
    statistics = compute_feature_statistics(dataset)

    print("\\n[QUALITATIVE GROUNDING]")

    for change in qualitative_changes:
        feature = change.get("feature")

        if feature in QUALITATIVE_EXCLUDED_FEATURES:
            raise ValueError(
                f"Qualitative modification is not supported for '{feature}': "
                "the dataset uses special encoded values."
            )

        if feature not in NUM_FEATURES:
            raise ValueError(
                f"Qualitative modification is not supported for "
                f"non-numeric or unknown feature '{feature}'."
            )

        if feature not in baseline or feature not in statistics:
            raise ValueError(f"Baseline/statistics unavailable for '{feature}'.")

        if feature in (features or {}):
            raise ValueError(
                f"Feature '{feature}' has both explicit and qualitative "
                "modifications; their combination is ambiguous."
            )

        direction = str(change.get("direction") or "").strip().lower()

        raw_magnitude = change.get("magnitude")

        if raw_magnitude is None or not str(raw_magnitude).strip():
            magnitude = "substantially"
        else:
            magnitude = str(raw_magnitude).strip().lower()

        if direction not in _DIRECTION_SIGN:
            raise ValueError(f"Unsupported qualitative direction: {direction!r}")

        if magnitude not in QUALITATIVE_SCALE:
            raise ValueError(f"Unsupported qualitative magnitude: {magnitude!r}")

        std = statistics[feature]["std"]
        if not math.isfinite(std) or std <= 0:
            raise ValueError(f"Invalid standard deviation for '{feature}': {std}")

        baseline_value = float(baseline[feature])
        requested_delta = (
            std * QUALITATIVE_SCALE[magnitude] * _DIRECTION_SIGN[direction]
        )
        requested_target = baseline_value + requested_delta
        effective_target = requested_target

        bounds = FEATURE_BOUNDS.get(feature)
        if bounds is not None:
            lower, upper = bounds
            if lower is not None:
                effective_target = max(lower, effective_target)
            if upper is not None:
                effective_target = min(upper, effective_target)

        effective_delta = effective_target - baseline_value

        modifications[feature] = {
            "type": "absolute_delta",
            "value": effective_delta,
        }
        grounded[feature] = effective_target

        print(
            f"Feature: {feature} | direction: {direction} | magnitude: {magnitude} | "
            f"baseline: {baseline_value:.8f} | std: {std:.8f} | "
            f"requested delta: {requested_delta:.8f} | "
            f"effective delta: {effective_delta:.8f} | "
            f"scenario value: {effective_target:.8f}"
        )

        if not math.isclose(requested_delta, effective_delta, rel_tol=1e-12, abs_tol=1e-12):
            print(
                f"[QUALITATIVE GROUNDING][BOUND APPLIED] {feature}: "
                f"{requested_target:.8f} adjusted to {effective_target:.8f}."
            )

    return grounded, modifications
