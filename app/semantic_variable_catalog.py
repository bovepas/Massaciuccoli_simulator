# -*- coding: utf-8 -*-
"""Semantic variable catalog for the Massaciuccoli Digital Twin.

Source: Vannini & Coro, "A multi-model generalisable ecosystem risk
assessment methodology for the Massaciuccoli Lake basin wetland", Table 1
and sections 3.1.2–3.1.3 in the article supplied with this conversation.

Important distinction from the source article:
- The paper collectively calls all 12 inputs "stressor variables".
- It classifies their ecological role as either `harmful_force` or
  `fragile_condition`. A fragile-condition indicator is NOT automatically a
  harmful pressure or a cause of degradation.

Mapping confidence is explicit because an Atlas variable's name is not always
identical to the application's CSV feature name. Entries marked provisional
must be checked against the CSV's data-description row and preprocessing.

This module depends only on the Python standard library.
"""

from copy import deepcopy
import re
import unicodedata
from typing import Any, Dict, List, Optional

CATALOG_VERSION = "1.1.0"
SCIENTIFIC_SOURCE = {
    "authors": ["Gian Luca Vannini", "Gianpaolo Coro"],
    "title": "A multi-model generalisable ecosystem risk assessment methodology for the Massaciuccoli Lake basin wetland",
    "source_item": "Table 1; sections 3.1.2–3.1.3",
    "pdf_pages": [54, 55],
}

# Every record uses the model's canonical feature name as `canonical_name`.
# `role` and `measurement_direction` reproduce the article's Table 1.
VARIABLE_CATALOG: List[Dict[str, Any]] = [
    {
        "canonical_name": "Density change in land imperviousness",
        "display_name": "Change in land imperviousness",
        "aliases": ["land imperviousness", "imperviousness increase", "soil sealing", "land sealing"],
        "atlas_id": 3,
        "atlas_name": "Land imperviousness density increase",
        "description": "Change in degree of land imperviousness, from -100% to +100%.",
        "data_type": "numeric",
        "role": "harmful_force",
        "measurement_direction": "direct",
        "unit": "%",
        "paper_encoding": "Stable non-built-up cells -> 100%; unclassifiable/outside area -> NA; other values -> as is.",
        "tags": ["stressor_variable", "harmful_force", "anthropogenic_pressure", "land_use", "imperviousness", "land_change"],
        "mapping_status": "probable_match_requires_encoding_check",
        "mapping_note": "The concept matches Atlas ID 3, but the article's mapping of stable non-built-up cells to 100% is non-intuitive. Verify actual CSV semantics and preprocessing before interpreting sign or magnitude.",
    },
    {
        "canonical_name": "Density of tree cover",
        "display_name": "Tree-cover density",
        "aliases": ["tree cover", "forest cover", "tree density", "forest density"],
        "atlas_id": 9,
        "atlas_name": "Tree cover density",
        "description": "Level of tree-cover density, from 0% to 100%.",
        "data_type": "numeric",
        "role": "fragile_condition",
        "measurement_direction": "direct",
        "unit": "%",
        "paper_encoding": "As is.",
        "tags": ["stressor_variable", "fragile_condition", "ecosystem_state", "vegetation", "habitat", "tree_cover", "forest"],
        "mapping_status": "strong_match",
        "mapping_note": "The application feature and Atlas name correspond directly. It is an ecosystem-state/fragile-condition indicator, not automatically a harmful force.",
    },
    {
        "canonical_name": "Change in tree cover density in the past decade",
        "display_name": "Tree-cover change over the past decade",
        "aliases": ["tree cover change", "tree-cover loss", "tree cover decrease", "forest cover loss", "change in forest cover"],
        "atlas_id": 10,
        "atlas_name": "Tree cover density decrease",
        "description": "Changes in tree-cover density across thematic classes: unchanged areas without tree cover, new tree cover, tree-cover loss, and unchanged areas with tree cover.",
        "data_type": "categorical",
        "role": "harmful_force",
        "measurement_direction": "inverse",
        "unit": "classes",
        "paper_encoding": "Unchanged without tree cover -> 0; new tree cover -> -1; tree-cover loss -> 1; unchanged with tree cover -> 0; other values -> 0.",
        "tags": ["stressor_variable", "harmful_force", "habitat_degradation", "vegetation", "tree_cover", "forest", "land_change"],
        "mapping_status": "probable_alias_requires_encoding_check",
        "mapping_note": "Likely corresponds to Atlas ID 10, but the Atlas feature specifically encodes a decrease/loss indicator while the application name is broader. Verify the CSV category codes.",
    },
    {
        "canonical_name": "Presence of grassland",
        "display_name": "Grassland presence",
        "aliases": ["grassland", "grassland habitat", "grassland cover", "presence of grassland habitat"],
        "atlas_id": 11,
        "atlas_name": "Grassland cover",
        "description": "Classification of grassland cover with two thematic classes: grassland and non-grassland.",
        "data_type": "categorical",
        "role": "fragile_condition",
        "measurement_direction": "direct",
        "unit": "classes",
        "paper_encoding": "Grassland -> 1; non-grassland -> 0.",
        "tags": ["stressor_variable", "fragile_condition", "ecosystem_state", "vegetation", "grassland", "habitat"],
        "mapping_status": "strong_match",
        "mapping_note": "The concept matches Atlas ID 11. This is a presence/class indicator, not a percentage of grassland area.",
    },
    {
        "canonical_name": "Change in grassland presence in the past decade",
        "display_name": "Grassland-cover change over the past decade",
        "aliases": ["grassland change", "grassland loss", "grassland decrease", "grassland gain", "change in grassland cover"],
        "atlas_id": 12,
        "atlas_name": "Grassland cover decrease",
        "description": "Changes in grassland cover across thematic classes, including grassland gain/loss, unchanged areas, and unverified gain/loss.",
        "data_type": "categorical",
        "role": "harmful_force",
        "measurement_direction": "inverse",
        "unit": "classes",
        "paper_encoding": "Unchanged non-grassland -> 0; grassland gain -> -1; loss -> 1; unchanged grassland -> 0; unverified gain -> -1; unverified loss -> 1; other values -> 0.",
        "tags": ["stressor_variable", "harmful_force", "habitat_degradation", "vegetation", "grassland", "habitat", "land_change"],
        "mapping_status": "probable_alias_requires_encoding_check",
        "mapping_note": "Likely corresponds to Atlas ID 12. Verify whether the current CSV stores Atlas classes, a simplified binary feature, or another encoding.",
    },
    {
        "canonical_name": "Land use and cover",
        "display_name": "Land use and cover — selected hazard classes",
        "aliases": ["land use", "land cover", "land use/land cover", "Natura 2000 hazard areas", "land use hazard area"],
        "atlas_id": 17,
        "atlas_name": "Land use and cover (Natura 2000) hazard area",
        "description": "Land use/cover in Natura 2000 sites, restricted to selected classes potentially harmful to natural ecosystems: industrial, commercial/military, mineral extraction, dumps/construction sites, and highly modified watercourses/canals.",
        "data_type": "categorical",
        "role": "harmful_force",
        "measurement_direction": "direct",
        "unit": "classes",
        "paper_encoding": "Selected hazard classes -> 1; other classes -> 0.",
        "tags": ["stressor_variable", "harmful_force", "anthropogenic_pressure", "land_use", "habitat_degradation", "infrastructure", "pollution"],
        "mapping_status": "provisional_mapping_requires_data_dictionary",
        "mapping_note": "The application's label is broad; Atlas ID 17 specifically represents selected hazard classes in Natura 2000 sites. Confirm the CSV description and categories before treating this as an exact match.",
    },
    {
        "canonical_name": "Index of total productivity by plant phenology",
        "display_name": "Plant productivity index",
        "aliases": ["plant productivity", "vegetation productivity", "phenology index", "ecosystem productivity", "vegetation growth"],
        "atlas_id": 40,
        "atlas_name": "Plant productivity",
        "description": "Sum of daily vegetation phenological-index values during the growing season; an annual estimate of accumulated plant biomass and ecosystem productivity.",
        "data_type": "numeric",
        "role": "fragile_condition",
        "measurement_direction": "direct",
        "unit": "index/range as stored in source",
        "paper_encoding": "As is.",
        "tags": ["stressor_variable", "fragile_condition", "ecosystem_state", "vegetation", "productivity", "phenology", "ecosystem_function"],
        "mapping_status": "strong_match_check_units",
        "mapping_note": "The concept matches Atlas ID 40. Confirm the unit/scale from the CSV metadata; do not automatically describe this index as a percentage.",
    },
    {
        "canonical_name": "Change in average temperature compared to a recent past",
        "display_name": "Temperature change relative to the reference period",
        "aliases": ["temperature", "temperature change", "temperature increase", "warming", "air temperature change"],
        "atlas_id": 57,
        "atlas_name": "Temperature increase",
        "description": "Absolute change in air temperature (approximately 2 m above ground) relative to the 1971–2010 average.",
        "data_type": "numeric",
        "role": "harmful_force",
        "measurement_direction": "direct",
        "unit": "°C",
        "paper_encoding": "As is.",
        "tags": ["stressor_variable", "harmful_force", "climate", "temperature", "climate_change", "thermal_stress"],
        "mapping_status": "strong_match_check_reference_period",
        "mapping_note": "The concept matches Atlas ID 57. Verify that the application's CSV uses the same 1971–2010 reference period.",
    },
    {
        "canonical_name": "Relative change in the potential evapotranspiration compared to a recent past",
        "display_name": "Potential evapotranspiration change",
        "aliases": ["evapotranspiration", "potential evapotranspiration", "PET", "evaporation change", "aridity indicator"],
        "atlas_id": 58,
        "atlas_name": "Potential evapotranspiration decrease",
        "description": "Relative change in potential evapotranspiration compared with the average across 1971–2010.",
        "data_type": "numeric",
        "role": "harmful_force",
        "measurement_direction": "inverse",
        "unit": "%",
        "paper_encoding": "As is, with the stressor defined inversely in the article's taxonomy.",
        "tags": ["stressor_variable", "harmful_force", "climate", "hydrology", "evapotranspiration", "aridity", "water_balance"],
        "mapping_status": "strong_concept_match_check_sign",
        "mapping_note": "The concepts match, but the application's feature name does not explicitly say 'decrease'. Verify the data sign convention and transformation; do not infer direction from the name alone.",
    },
    {
        "canonical_name": "Cumulative change in precipitation compared to a recent past",
        "display_name": "Precipitation change",
        "aliases": ["precipitation", "rain", "rainfall", "precipitation decrease", "rainfall change"],
        "atlas_id": 59,
        "atlas_name": "Precipitation decrease",
        "description": "Relative change in precipitation per unit area compared with the average across 1971–2010.",
        "data_type": "numeric",
        "role": "harmful_force",
        "measurement_direction": "inverse",
        "unit": "%",
        "paper_encoding": "As is, with the stressor defined inversely in the article's taxonomy.",
        "tags": ["stressor_variable", "harmful_force", "climate", "hydrology", "precipitation", "aridity", "water_balance"],
        "mapping_status": "strong_concept_match_check_sign",
        "mapping_note": "The concepts match, but the application's feature name does not explicitly say 'decrease'. Verify the data sign convention and transformation; do not infer direction from the name alone.",
    },
    {
        "canonical_name": "Number of species potentially living in the cell",
        "display_name": "Potential species richness",
        "aliases": ["biodiversity", "species richness", "number of species", "species count", "potential species richness"],
        "atlas_id": 65,
        "atlas_name": "Species richness",
        "description": "Biodiversity index based on cumulative species richness, including birds, fish/crustaceans, insects/clams, mammals, reptiles/amphibians, and other groups.",
        "data_type": "numeric",
        "role": "fragile_condition",
        "measurement_direction": "direct",
        "unit": "number of species / index as defined by source",
        "paper_encoding": "As is.",
        "tags": ["stressor_variable", "fragile_condition", "ecosystem_state", "biodiversity", "species_richness", "ecological_indicator"],
        "mapping_status": "strong_concept_match",
        "mapping_note": "The concept matches Atlas ID 65. The application's name does not make this a direct field observation, abundance estimate, or complete biodiversity census.",
    },
    {
        "canonical_name": "Change in land use and cover in the past decade",
        "display_name": "Land-use anthropisation change",
        "aliases": ["land use change", "land-use change", "anthropisation increase", "land-use anthropisation", "land cover change"],
        "atlas_id": 147,
        "atlas_name": "Land use and cover anthropisation increase",
        "description": "Changes in land use and vegetation cover, selecting classes with potential ecosystem impact: artificially shaped territories, utilised agricultural areas, and water bodies.",
        "data_type": "categorical",
        "role": "harmful_force",
        "measurement_direction": "direct",
        "unit": "classes",
        "paper_encoding": "Artificially shaped territories -> 1; utilised agricultural areas -> 0.5; water bodies -> -1; other classes -> 0.",
        "tags": ["stressor_variable", "harmful_force", "anthropogenic_pressure", "land_use", "land_change", "anthropisation"],
        "mapping_status": "probable_alias_requires_encoding_check",
        "mapping_note": "Likely corresponds to Atlas ID 147, but the application's label is more general than the paper's anthropisation indicator. Verify the source CSV description and codes.",
    },
]

# Model-CSV descriptions captured from the user-provided second-row data dictionary.
# This metadata records what the application CSV says; it is kept separate from
# the paper's Table 1 because some class mappings / unit descriptions differ.
APPLICATION_CSV_METADATA: Dict[str, Dict[str, Any]] = {
    "Density change in land imperviousness": {
        "description": "Sealing density change in percentage during the past decade.",
        "unit": "%",
        "encoding": "Values over 100 represent unchanged situations.",
        "interpretation_limits": [
            "Do not read values over 100 as a literal percentage increase; the CSV description says they mark unchanged situations.",
            "Check the preprocessing convention before interpreting sign or magnitude as increasing imperviousness."
        ],
    },
    "Density of tree cover": {
        "description": "Current level of tree-cover density in the cell.",
        "unit": "%",
        "encoding": "Percentage; the CSV describes the current level.",
        "interpretation_limits": [
            "This is a state/fragility indicator in the paper, not automatically a harmful pressure.",
            "A high value should not be described as causing higher risk without reference to the risk methodology."
        ],
    },
    "Change in tree cover density in the past decade": {
        "description": "Change in tree-cover density over the past decade; NA marks areas with no tree-cover density.",
        "unit": "categorical classes",
        "encoding": "0=unchanged areas; 1=new tree cover; 2=tree-cover loss; 10=unchanged areas with tree cover; NA=areas with no tree-cover density (per CSV description).",
        "interpretation_limits": [
            "The application's class codes differ from the simplified normalised encoding described in the paper; use the CSV codes when describing this input.",
            "Do not interpret the class codes as ordered numeric magnitudes."
        ],
    },
    "Presence of grassland": {
        "description": "Current presence or absence of grassland in the cell.",
        "unit": "binary class",
        "encoding": "1=grassland present; 0=grassland absent.",
        "interpretation_limits": [
            "This is a binary presence feature, not grassland area percentage or continuous coverage.",
            "A request to reduce grassland coverage by a percentage is not directly representable by this feature alone."
        ],
    },
    "Change in grassland presence in the past decade": {
        "description": "Change in grassland vegetation cover in the past decade.",
        "unit": "categorical classes",
        "encoding": "0 and 10=unchanged; 1 and 11=grassland gain; 2 and 22=grassland loss (per CSV description).",
        "interpretation_limits": [
            "The application's class codes differ from the simplified encoding in the paper; do not silently substitute one encoding for the other.",
            "Codes represent classes, not percentages of grassland gained or lost."
        ],
    },
    "Land use and cover": {
        "description": "Current land-use/land-cover scenario.",
        "unit": "categorical land-cover code",
        "encoding": "1120=industrial/commercial/military units; 1310=mineral extraction, dump and construction sites; 8120=highly modified watercourses/canals; NA=areas uncovered by land or unused; other values=rural or naturalistic areas (per CSV description).",
        "interpretation_limits": [
            "The CSV describes CORINE-like categories, while the paper's Atlas ID 17 describes selected hazard classes in Natura 2000 sites; exact equivalence is not established.",
            "Do not treat category codes as a continuous numeric scale."
        ],
    },
    "Index of total productivity by plant phenology": {
        "description": "Growing-season integral: sum of daily plant-phenology index values between the season's start and end, representing overall vegetation growth.",
        "unit": "days (as stated in the application CSV description; verify precise interpretation)",
        "encoding": "Numeric growing-season integral, as stored in the input data.",
        "interpretation_limits": [
            "The paper describes an annual integrated productivity index; the application's stated unit is 'days'. Preserve that wording but verify the precise unit before reporting scientific units externally.",
            "Do not reinterpret this as a percentage without source documentation."
        ],
    },
    "Change in average temperature compared to a recent past": {
        "description": "Current average annual air-temperature change at about 2 m above ground relative to the 1971–2010 reference period.",
        "unit": "°C",
        "encoding": "Signed absolute temperature change relative to the reference period, according to the CSV description.",
        "interpretation_limits": [
            "This is a change relative to a reference period, not an absolute current air temperature.",
            "A positive value indicates warming relative to the reference period, according to the source description."
        ],
    },
    "Relative change in the potential evapotranspiration compared to a recent past": {
        "description": "Potential evapotranspiration indicator relative to the 1971–2010 reference period; the CSV describes the annual evaporative amount under sufficient water provisioning and calls the value an absolute change.",
        "unit": "% (as stated in the application CSV description)",
        "encoding": "Signed percentage change according to the CSV description; the paper treats a decrease in PET as an inverse harmful-force indicator.",
        "interpretation_limits": [
            "The CSV wording mixes 'relative change' with 'absolute change'; retain this ambiguity until the data-generation code is checked.",
            "Do not assume the sign has already been inverted in the application feature."
        ],
    },
    "Cumulative change in precipitation compared to a recent past": {
        "description": "Precipitation amount relative to the 1971–2010 reference period; the CSV describes rain, snow, sleet and hail and calls the value an absolute change.",
        "unit": "% (as stated in the application CSV description)",
        "encoding": "Signed percentage change according to the CSV description; the paper treats precipitation decrease as an inverse harmful-force indicator.",
        "interpretation_limits": [
            "The CSV wording mixes 'relative change' with 'absolute change'; retain this ambiguity until the data-generation code is checked.",
            "Do not assume the sign has already been inverted in the application feature."
        ],
    },
    "Number of species potentially living in the cell": {
        "description": "Potential species-richness index for birds, fish, crustaceans, insects, clams, mammals, reptiles, amphibians and other animals that may occur in the spatial cell.",
        "unit": "number of species / index as defined by source",
        "encoding": "Numeric species-richness indicator, as stored in the input data.",
        "interpretation_limits": [
            "This is a potential species-richness indicator, not necessarily a direct observation, abundance estimate or complete biodiversity census.",
            "In the paper it is a fragile condition to preserve, not a harmful force."
        ],
    },
    "Change in land use and cover in the past decade": {
        "description": "Land-use/land-cover change over the past decade, classified according to the Corine Land Cover inventory (level III and partially IV).",
        "unit": "categorical classes",
        "encoding": "1=artificially shaped territories; 2=agricultural surfaces; NA and 0=no change or other land-use types such as woodland, natural areas, wetlands and watercourses (per CSV description).",
        "interpretation_limits": [
            "The CSV encoding differs from the article's Atlas ID 147 mapping (which includes a 0.5 agricultural class and -1 water bodies); do not mix encodings.",
            "Codes are categorical meanings, not a continuous intensity scale unless the active model preprocessing explicitly defines them as such."
        ],
    },
}

ROLE_DEFINITIONS = {
    "harmful_force": (
        "In the supplied paper, a variable representing a direct driver with a "
        "potentially negative impact on habitats and possible structural or "
        "functional changes. This is the paper's role classification, not proof "
        "that a specific local causal effect has been estimated."
    ),
    "fragile_condition": (
        "In the supplied paper, an indicator of an ecosystem condition associated "
        "with sensitivity or resilience. It describes an ecological state to "
        "preserve or a condition relevant to vulnerability; it is not itself "
        "automatically a harmful pressure."
    ),
}

TAG_DEFINITIONS = {
    "stressor_variable": "One of the 12 input variables treated collectively as stressor variables by the paper's risk-assessment methodology.",
    "harmful_force": ROLE_DEFINITIONS["harmful_force"],
    "fragile_condition": ROLE_DEFINITIONS["fragile_condition"],
    "anthropogenic_pressure": "A variable representing a human-driven land-use or territorial pressure; interpret only in the scope defined by the source encoding.",
    "climate": "A climatic driver/indicator; not by itself proof of ecological impact in a specific cell.",
    "ecosystem_state": "A state or condition indicator of habitat or ecosystem components.",
    "ecosystem_function": "An indicator related to an ecosystem process or function; does not imply that all ecosystem functions are measured.",
}

# These columns exist in the broader CSV/table description but are not among
# the 12 canonical model input features in VARIABLE_CATALOG.
NON_FEATURE_DATASET_FIELDS: List[Dict[str, Any]] = [
    {
        "canonical_name": "Longitude",
        "role": "spatial_metadata",
        "unit": "decimal degrees (WGS84)",
        "used_as_model_feature": False,
    },
    {
        "canonical_name": "Latitude",
        "role": "spatial_metadata",
        "unit": "decimal degrees (WGS84)",
        "used_as_model_feature": False,
    },
    {
        "canonical_name": "Ecosystem risk classification according to a Variational Autoencoder with a later application of a Multi K-means process",
        "role": "model_output",
        "unit": "categorical risk class",
        "used_as_model_feature": False,
        "interpretation_limits": [
            "This is a model output, not one of the 12 environmental input features.",
            "Its exact low/medium/high class semantics are defined by the risk pipeline, not by the generic input-variable catalog."
        ],
    },
]

# Add the separate application-side metadata to each canonical record without
# replacing the article's original description, units or encoding.
for _record in VARIABLE_CATALOG:
    _csv_metadata = APPLICATION_CSV_METADATA.get(_record["canonical_name"], {})
    _record["application_csv_description"] = _csv_metadata.get("description")
    _record["application_csv_unit"] = _csv_metadata.get("unit")
    _record["application_csv_encoding"] = _csv_metadata.get("encoding")
    _record["interpretation_limits"] = list(_csv_metadata.get("interpretation_limits", []))
    _record["role_definition"] = ROLE_DEFINITIONS.get(_record["role"], "")
    _record["role_source"] = "Vannini & Coro, Table 1 (Atlas variable mapping status applies)"

# Public aliases allow natural-language expressions to resolve to canonical names.
_BY_CANONICAL = {item["canonical_name"]: item for item in VARIABLE_CATALOG}
_BY_ATLAS_ID = {item["atlas_id"]: item for item in VARIABLE_CATALOG}
_ALIASES: Dict[str, str] = {}
for _item in VARIABLE_CATALOG:
    for _name in [_item["canonical_name"], _item["display_name"], _item["atlas_name"]] + _item.get("aliases", []):
        _ALIASES[_name] = _item["canonical_name"]


def _normalise_label(value: str) -> str:
    """Case-, punctuation- and diacritic-insensitive key normalisation."""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().strip()
    value = re.sub(r"[_\-–—]+", " ", value)
    value = re.sub(r"[^\w\s%°]+", " ", value)
    return " ".join(value.split())


_NORMALIZED_ALIASES = {
    _normalise_label(alias): canonical for alias, canonical in _ALIASES.items()
}


def get_variable_catalog() -> List[Dict[str, Any]]:
    """Return a deep copy of all records so caller mutations cannot alter globals."""
    return deepcopy(VARIABLE_CATALOG)


def get_variable(name: str) -> Optional[Dict[str, Any]]:
    """Look up a variable by canonical name, display name, Atlas name, or alias."""
    if not name:
        return None
    canonical = _NORMALIZED_ALIASES.get(_normalise_label(name))
    if canonical is None:
        return None
    return deepcopy(_BY_CANONICAL[canonical])


def get_variables_by_tag(tag: str) -> List[Dict[str, Any]]:
    """Return all records with an exact semantic tag."""
    wanted = str(tag).strip().casefold()
    return [deepcopy(item) for item in VARIABLE_CATALOG if wanted in item["tags"]]


def get_stressor_variables() -> List[Dict[str, Any]]:
    """Return all 12 variables treated as stressor variables by the paper."""
    return get_variables_by_tag("stressor_variable")


def get_harmful_forces() -> List[Dict[str, Any]]:
    """Return only variables classified as harmful forces, not fragile conditions."""
    return get_variables_by_tag("harmful_force")


def get_fragile_conditions() -> List[Dict[str, Any]]:
    """Return indicators classified as fragile ecosystem conditions."""
    return get_variables_by_tag("fragile_condition")


def get_provisional_mappings() -> List[Dict[str, Any]]:
    """Return entries whose Atlas-to-application mapping needs further validation."""
    return [
        deepcopy(item) for item in VARIABLE_CATALOG
        if "requires" in item["mapping_status"] or "check_" in item["mapping_status"]
    ]


def get_catalog_summary() -> Dict[str, Any]:
    """Return a compact summary suitable for prompts, logs, and tests."""
    return {
        "catalog_version": CATALOG_VERSION,
        "source": deepcopy(SCIENTIFIC_SOURCE),
        "total_variables": len(VARIABLE_CATALOG),
        # Application meaning: an environmental stressor is a harmful force.
        "stressor_variables": len(get_harmful_forces()),
        # Retain the source-paper terminology separately for traceability.
        "paper_stressor_inputs": len(get_stressor_variables()),
        "harmful_forces": len(get_harmful_forces()),
        "fragile_conditions": len(get_fragile_conditions()),
        "mappings_requiring_checks": len(get_provisional_mappings()),
        "supported_data_intents": sorted(DATA_INTENT_TAGS.keys()),
        "taxonomy_note": (
            "The paper collectively calls all 12 inputs stressor variables, but this "
            "application operationally defines environmental stressors as harmful_force "
            "records only. Fragile-condition indicators are excluded from that request category."
        ),
    }


def format_variable_for_prompt(name: str) -> Optional[str]:
    """Build a grounded semantic description for LLM context; does not infer effects."""
    item = get_variable(name)
    if item is None:
        return None
    return (
        f"Canonical feature: {item['canonical_name']}\n"
        f"Display name: {item['display_name']}\n"
        f"Atlas reference: {item['atlas_id']} — {item['atlas_name']}\n"
        f"Description: {item['description']}\n"
        f"Ecological role: {item['role']}\n"
        f"Role definition: {item.get('role_definition', '')}\n"
        f"Tags: {', '.join(item['tags'])}\n"
        f"Data type: {item['data_type']}; paper unit: {item['unit']}\n"
        f"Application CSV description: {item.get('application_csv_description', '')}\n"
        f"Application CSV unit: {item.get('application_csv_unit', '')}\n"
        f"Application CSV encoding: {item.get('application_csv_encoding', '')}\n"
        f"Measurement direction in paper: {item['measurement_direction']}\n"
        f"Mapping status: {item['mapping_status']}\n"
        f"Mapping note: {item['mapping_note']}\n"
        f"Interpretation limits: {'; '.join(item.get('interpretation_limits', []))}"
    )


# ======================================================
# QUERY-AWARE CATALOG ACCESS FOR TASKS SUCH AS `data`
# ======================================================

# Intent -> tags used to select relevant records. `None` means all input features.
DATA_INTENT_TAGS = {
    "dataset_inventory": None,
    # Project convention: “environmental stressors” means harmful forces only.
    # The source paper labels all 12 model inputs collectively as stressors, but
    # this query category deliberately excludes fragile-condition indicators.
    "stressor_variables": ("harmful_force",),
    "harmful_forces": ("harmful_force",),
    "fragile_conditions": ("fragile_condition",),
    "anthropogenic_pressures": ("anthropogenic_pressure",),
    "climate_drivers": ("climate",),
    "ecological_indicators": ("ecosystem_state", "ecological_indicator"),
    # This asks for direct function/productivity-related indicators, with a
    # guidance note that supporting state indicators must not be over-described.
    "ecosystem_functioning": ("ecosystem_function",),
    # Broad synthesis: include variables connected to any of these domains.
    "ecological_dynamics": (
        "climate", "hydrology", "land_change", "tree_cover", "grassland",
        "productivity", "biodiversity", "vegetation", "land_use",
    ),
}

DATA_INTENT_GUIDANCE = {
    "dataset_inventory": (
        "List the canonical model input variables grouped by ecological domain. "
        "Do not imply all variables are harmful stressors. Separate input variables "
        "from coordinates and the ecosystem-risk model output."
    ),
    "stressor_variables": (
        "In this application, interpret environmental stressors as variables whose "
        "catalog role is harmful_force. Return only these records and exclude all "
        "fragile_condition indicators. The source paper uses the term stressor variables "
        "collectively for all 12 model inputs, but this query follows the project's narrower "
        "operational definition. Describe these as potential harmful drivers, not as proven "
        "causal effects in every grid cell."
    ),
    "harmful_forces": (
        "Return only records whose role is harmful_force. Explain these as potential "
        "negative drivers under the paper's framework, not as proven causal effects "
        "for every grid cell. Do not include fragile-condition variables in this list."
    ),
    "fragile_conditions": (
        "Return only fragile-condition indicators. Explain these as ecological states "
        "or conditions relevant to sensitivity/resilience and worth preserving, not as "
        "harmful pressures in themselves."
    ),
    "anthropogenic_pressures": (
        "Use only variables tagged anthropogenic_pressure. Respect the class mapping "
        "and report provisional Atlas-to-CSV mappings as uncertain. Do not infer a "
        "measured causal effect unless the user asks a different task and evidence supports it."
    ),
    "climate_drivers": (
        "Describe climate-related variables as drivers/indicators. Preserve reference "
        "periods, units and sign ambiguities. A feature name alone does not prove a local impact."
    ),
    "ecological_indicators": (
        "Describe indicators of ecosystem state and ecological conditions. Distinguish "
        "state indicators from external drivers and from measured outcomes."
    ),
    "ecosystem_functioning": (
        "The catalog has a direct productivity-related indicator, not a comprehensive "
        "measurement of all ecosystem functions. Explain this limitation and separately "
        "mention related state indicators only if relevant."
    ),
    "ecological_dynamics": (
        "Organise relevant inputs by climate, land/habitat change, vegetation, "
        "productivity and biodiversity. Explain what each group describes without "
        "asserting causal mechanisms that the dataset does not estimate."
    ),
}


def classify_data_query_intent(question: str) -> Optional[str]:
    """Classify broad catalog questions for the `data` task; return None otherwise.

    This is a lightweight deterministic gate, not an ecological inference engine.
    Specific semantic intents are tested before generic inventory wording so that
    'stressors' or 'ecosystem functioning' questions are not collapsed into a list.
    """
    q = _normalise_label(question or "")
    if not q:
        return None

    # Do not capture questions that are asking for relationships, ranking,
    # impact or prediction rather than a catalog explanation.
    relationship_markers = (
        "most strongly associated", "correlation", "correlate", "influence",
        "affect", "effect of", "drivers of", "contributes most", "impact on",
        "reduce risk", "increase risk", "risk under a scenario",
    )
    has_relationship_intent = any(marker in q for marker in relationship_markers)

    # Specific catalog taxonomies have precedence over generic inventory phrases.
    if any(term in q for term in (
        "harmful forces", "harmful force", "pressioni dannose", "forze dannose",
        "harmful drivers",
    )):
        return "harmful_forces"

    if any(term in q for term in (
        "anthropogenic pressures", "anthropogenic pressure", "human pressures",
        "human pressure", "pressures caused by human", "pressioni antropiche",
        "pressioni umane",
    )):
        return "anthropogenic_pressures"

    if any(term in q for term in (
        "fragile conditions", "fragile condition", "ecological fragility",
        "fragility conditions", "condizioni di fragilita", "fragilita ecologica",
    )):
        return "fragile_conditions"

    if any(term in q for term in (
        "environmental stressors", "ecological stressors", "stressor variables",
        "stressor variable", "stressors in the dataset", "stressors are measured",
        "which stressors", "what stressors", "stressori", "fattori di stress",
    )):
        return "stressor_variables"

    if any(term in q for term in (
        "climate drivers", "climatic drivers", "climate stressors",
        "climatic stressors", "climate-related variables", "climate related variables",
        "variabili climatiche", "stressori climatici",
    )) and not has_relationship_intent:
        return "climate_drivers"

    if any(term in q for term in (
        "ecosystem functioning", "ecosystem functions", "functioning of the ecosystem",
        "ecosystem function", "funzionamento dell ecosistema", "funzioni ecosistemiche",
    )) and not has_relationship_intent:
        return "ecosystem_functioning"

    if any(term in q for term in (
        "ecological dynamics", "ecosystem dynamics", "dynamics of the basin",
        "ecological processes", "ecological dynamics of the basin",
        "dinamiche ecologiche", "dinamiche dell ecosistema", "processi ecologici",
    )) and not has_relationship_intent:
        return "ecological_dynamics"

    if any(term in q for term in (
        "ecological variables", "ecological indicators", "habitat indicators",
        "ecological conditions", "indicatori ecologici", "variabili ecologiche",
        "condizioni ecologiche",
    )) and not has_relationship_intent:
        return "ecological_indicators"

    # Generic inventory wording; only match when the request is clearly about
    # availability/contents, not just any sentence containing 'variables'.
    inventory_markers = (
        "available in the dataset", "available in dataset", "included in the dataset",
        "included in dataset", "explicitly measured in the dataset",
        "explicitly included in the dataset", "represented in the dataset",
        "variables in the dataset", "dataset variables", "what variables are available",
        "which variables are available", "what data does the dataset contain",
        "what data are in the dataset", "all available variables", "all variables",
        "quali variabili sono disponibili", "quali variabili contiene il dataset",
        "quali dati contiene il dataset", "variabili presenti nel dataset",
    )
    if any(marker in q for marker in inventory_markers) and not has_relationship_intent:
        return "dataset_inventory"

    return None


def get_variables_for_intent(intent: str) -> List[Dict[str, Any]]:
    """Return catalog records relevant to one recognized data intent."""
    if intent not in DATA_INTENT_TAGS:
        raise ValueError(
            f"Unknown data catalog intent {intent!r}. Supported: {', '.join(DATA_INTENT_TAGS)}"
        )
    tags = DATA_INTENT_TAGS[intent]
    if tags is None:
        return get_variable_catalog()
    return [
        deepcopy(item) for item in VARIABLE_CATALOG
        if any(tag in item["tags"] for tag in tags)
    ]


def build_catalog_context(intent: str, variable_names: Optional[List[str]] = None) -> str:
    """Build a compact, traceable context block for the task's LLM explanation.

    The CSV itself remains unchanged. This function provides semantic metadata only;
    it does not compute values or infer effects from observed numbers.
    """
    if intent not in DATA_INTENT_TAGS:
        raise ValueError(
            f"Unknown data catalog intent {intent!r}. Supported: {', '.join(DATA_INTENT_TAGS)}"
        )

    if variable_names:
        variables = []
        for name in variable_names:
            item = get_variable(name)
            if item is not None:
                variables.append(item)
    else:
        variables = get_variables_for_intent(intent)

    if intent == "stressor_variables":
        taxonomy_lines = [
            "Application convention: environmental stressors means harmful_force records only.",
            "Exclude fragile_condition indicators from this category, even though the source paper",
            "collectively calls all 12 model inputs stressor variables.",
        ]
    else:
        taxonomy_lines = [
            "Source taxonomy: the article treats the 12 model inputs collectively as stressor variables,",
            "but distinguishes harmful_force (potentially harmful driver) from fragile_condition",
            "(ecosystem state/fragility indicator). These roles must not be conflated.",
        ]

    lines = [
        "MASSACIUCCOLI SEMANTIC VARIABLE CATALOG",
        f"Catalog version: {CATALOG_VERSION}",
        f"Detected data intent: {intent}",
        f"Scientific source: {SCIENTIFIC_SOURCE['authors'][0]} and {SCIENTIFIC_SOURCE['authors'][1]}, ",
        f"{SCIENTIFIC_SOURCE['title']}; {SCIENTIFIC_SOURCE['source_item']}.",
        *taxonomy_lines,
        "Mapping status matters: mappings not marked strong_match can differ between Atlas and application CSV.",
        "",
        "INTENT-SPECIFIC INSTRUCTIONS:",
        DATA_INTENT_GUIDANCE[intent],
        "",
        f"RELEVANT VARIABLES ({len(variables)}):",
    ]

    if not variables:
        lines.append("No variables matched the requested intent. Do not invent a match.")

    for item in variables:
        lines.extend([
            f"- {item['display_name']} [canonical_name={item['canonical_name']}]",
            f"  Article role: {item['role']} — {item.get('role_definition', '')}",
            f"  Description in article: {item['description']}",
            f"  Description in application CSV: {item.get('application_csv_description') or 'not provided'}",
            f"  Tags: {', '.join(item['tags'])}",
            f"  Data type: {item['data_type']}; article unit: {item['unit']}; application CSV unit: {item.get('application_csv_unit') or 'not provided'}",
            f"  CSV encoding: {item.get('application_csv_encoding') or 'not provided'}",
            f"  Atlas mapping status: {item['mapping_status']} — {item['mapping_note']}",
            f"  Interpretation limits: {'; '.join(item.get('interpretation_limits', [])) or 'No additional variable-specific limits recorded.'}",
        ])

    if intent == "dataset_inventory":
        lines.extend([
            "",
            "NON-FEATURE DATASET FIELDS (not part of the 12 model inputs):",
        ])
        for field in NON_FEATURE_DATASET_FIELDS:
            lines.append(
                f"- {field['canonical_name']}: role={field['role']}; unit={field['unit']}; used_as_model_feature={field['used_as_model_feature']}"
            )

    return "\n".join(lines)


def get_data_intent_guidance(intent: str) -> str:
    """Return the response-writing guardrails for a classified data intent."""
    if intent not in DATA_INTENT_GUIDANCE:
        raise ValueError(f"Unknown data catalog intent: {intent!r}")
    return DATA_INTENT_GUIDANCE[intent]


if __name__ == "__main__":
    print("Massaciuccoli semantic variable catalog")
    print("-" * 42)
    for key, value in get_catalog_summary().items():
        print(f"{key}: {value}")
    for role in ("harmful_force", "fragile_condition"):
        records = [v for v in VARIABLE_CATALOG if v["role"] == role]
        print(f"\n{role} ({len(records)}):")
        for item in records:
            print(f"  - {item['canonical_name']} (Atlas ID {item['atlas_id']})")
