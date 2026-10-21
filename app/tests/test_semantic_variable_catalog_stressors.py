"""Smoke tests for the Massaciuccoli semantic variable catalog APIs."""
import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("semantic_variable_catalog_stressors_fixed.py")
spec = importlib.util.spec_from_file_location("semantic_variable_catalog", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

summary = mod.get_catalog_summary()
assert summary["total_variables"] == 12
assert summary["stressor_variables"] == 8
assert summary["paper_stressor_inputs"] == 12
assert summary["harmful_forces"] == 8
assert summary["fragile_conditions"] == 4

cases = {
    "Which environmental variables are available in the dataset?": "dataset_inventory",
    "Which environmental stressors are explicitly measured in the dataset?": "stressor_variables",
    "Which harmful forces are included?": "harmful_forces",
    "Which anthropogenic pressures are present?": "anthropogenic_pressures",
    "Which variables capture the main ecological dynamics of the basin?": "ecological_dynamics",
    "Which aspects of ecosystem functioning are represented in the dataset?": "ecosystem_functioning",
    "Which ecological variables are represented in the dataset?": "ecological_indicators",
    "Quali sono gli stressori ambientali nel dataset?": "stressor_variables",
    "Quali pressioni antropiche sono presenti?": "anthropogenic_pressures",
    "Which environmental variables are most strongly associated with biodiversity?": None,
    "What is the current state of the lake?": None,
}
for question, expected in cases.items():
    assert mod.classify_data_query_intent(question) == expected, (
        question, mod.classify_data_query_intent(question), expected
    )

assert len(mod.get_variables_for_intent("dataset_inventory")) == 12
stressor_records = mod.get_variables_for_intent("stressor_variables")
assert len(stressor_records) == 8
assert all(record["role"] == "harmful_force" for record in stressor_records)
assert len(mod.get_stressor_variables()) == 12  # source-paper terminology remains traceable
assert len(mod.get_variables_for_intent("harmful_forces")) == 8
assert len(mod.get_variables_for_intent("fragile_conditions")) == 4
assert len(mod.get_variables_for_intent("anthropogenic_pressures")) == 3
assert len(mod.get_variables_for_intent("climate_drivers")) == 3
assert len(mod.get_variables_for_intent("ecosystem_functioning")) == 1
assert mod.get_variable("temperature")["canonical_name"] == "Change in average temperature compared to a recent past"
assert "fragile_condition" in mod.get_variable("Presence of grassland")["tags"]
assert "CSV encoding" in mod.build_catalog_context("harmful_forces")
stressor_context = mod.build_catalog_context("stressor_variables")
assert "environmental stressors means harmful_force records only" in stressor_context
assert "RELEVANT VARIABLES (8)" in stressor_context
assert "NON-FEATURE DATASET FIELDS" in mod.build_catalog_context("dataset_inventory")
print("PASS: catalog import, tag counts, aliases, intent routing, and prompt context.")
