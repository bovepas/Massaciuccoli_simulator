import numpy as np
import pandas as pd

from utils.dependency_utils import compute_risk_perturbation_sensitivity


class FakeModel:
    def predict(self, frame):
        # Temperature is the only numeric feature used by this test.
        return np.clip(frame["Change in average temperature compared to a recent past"].astype(float) / 100.0, 0, 1)


def test_q25_q75_increase_and_spatial_aggregation(monkeypatch):
    import versions.v6_1_emulator as emulator
    monkeypatch.setattr(emulator, "NUM_FEATURES", ["Change in average temperature compared to a recent past"])
    monkeypatch.setattr(emulator, "CAT_FEATURES", [])
    monkeypatch.setattr(emulator, "preprocess_semantic_features", lambda frame: frame)

    feature = "Change in average temperature compared to a recent past"
    dataset = pd.DataFrame({feature: np.arange(100, dtype=float)})
    result = compute_risk_perturbation_sensitivity(
        source=feature,
        model=FakeModel(),
        dataset=dataset,
        direction="increase",
        batch_size=25,
    )
    assert result["perturbation"]["from_value"] == 24.75
    assert result["perturbation"]["to_value"] == 74.25
    assert result["mean_delta_risk"] > 0
    assert result["positive_response_fraction"] == 1.0
    assert result["negative_response_fraction"] == 0.0


def test_q25_q75_decrease_reverses_response(monkeypatch):
    import versions.v6_1_emulator as emulator
    monkeypatch.setattr(emulator, "NUM_FEATURES", ["Change in average temperature compared to a recent past"])
    monkeypatch.setattr(emulator, "CAT_FEATURES", [])
    monkeypatch.setattr(emulator, "preprocess_semantic_features", lambda frame: frame)

    feature = "Change in average temperature compared to a recent past"
    dataset = pd.DataFrame({feature: np.arange(100, dtype=float)})
    result = compute_risk_perturbation_sensitivity(
        source=feature,
        model=FakeModel(),
        dataset=dataset,
        direction="decrease",
    )
    assert result["perturbation"]["from_value"] == 74.25
    assert result["perturbation"]["to_value"] == 24.75
    assert result["mean_delta_risk"] < 0
    assert result["negative_response_fraction"] == 1.0
