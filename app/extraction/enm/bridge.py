from extraction.enm.schema import ENMExtraction


# ======================================================
# ENM EXTRACTION → TASK INPUTS
# ======================================================

# Maps user-facing biological categories to the actual
# category folders used by the ENM presence dataset.

CATEGORY_MAP = {
    "fish": "pesci_crostacei",
    "fishes": "pesci_crostacei",
    "pesce": "pesci_crostacei",
    "pesci": "pesci_crostacei",
    "crustaceans": "pesci_crostacei",
    "crustacean": "pesci_crostacei",
    "crostaceo": "pesci_crostacei",
    "crostacei": "pesci_crostacei",

    "bird": "uccelli",
    "birds": "uccelli",
    "uccello": "uccelli",
    "uccelli": "uccelli",

    "reptile": "rettili_anfibi",
    "reptiles": "rettili_anfibi",
    "rettile": "rettili_anfibi",
    "rettili": "rettili_anfibi",
    "amphibian": "rettili_anfibi",
    "amphibians": "rettili_anfibi",
    "anfibio": "rettili_anfibi",
    "anfibi": "rettili_anfibi",

    "insect": "insetti_molluschi",
    "insects": "insetti_molluschi",
    "insetto": "insetti_molluschi",
    "insetti": "insetti_molluschi",
    "mollusc": "insetti_molluschi",
    "molluscs": "insetti_molluschi",
    "mollusco": "insetti_molluschi",
    "molluschi": "insetti_molluschi",
    "invertebrates": "insetti_molluschi",
    "invertebrati": "insetti_molluschi",

    "mammal": "mammiferi",
    "mammals": "mammiferi",
    "mammifero": "mammiferi",
    "mammiferi": "mammiferi",
}


def enm_extraction_to_inputs(
    extraction: ENMExtraction,
) -> dict:
    """
    Convert ENMExtraction into the normalized input
    structure used by the ENM task.

    This bridge does not execute MaxEnt, apply scenario
    defaults, or interpret hypothetical raster changes.
    """

    if extraction is None:
        raise ValueError("ENM extraction is None")

    if not extraction.target:
        raise ValueError("No ENM target extracted")

    if extraction.target_type not in ("species", "category"):
        raise ValueError(
            f"Unexpected target_type: {extraction.target_type}"
        )

    target = extraction.target.strip()

    if not target:
        raise ValueError("ENM target is empty")

    dataset_group = None

    if extraction.target_type == "category":
        dataset_group = CATEGORY_MAP.get(target.casefold())

        if dataset_group is None:
            raise ValueError(
                f"Unsupported ENM category: {target}"
            )

    if extraction.intent == "future_suitability":
        if extraction.year not in (None, 2050, 2100):
            raise ValueError(
                f"Unsupported ENM scenario year: {extraction.year}"
            )

        if extraction.rcp not in (None, "rcp45", "rcp85"):
            raise ValueError(
                f"Unsupported ENM RCP: {extraction.rcp}"
            )

    if extraction.intent == "hypothetical_effect":
        if not extraction.variable:
            raise ValueError(
                "Hypothetical ENM effect requires a variable"
            )

        if extraction.variation is None:
            raise ValueError(
                "Hypothetical ENM effect requires a variation"
            )

        if extraction.variation_type is None:
            raise ValueError(
                "Hypothetical ENM effect requires a variation_type"
            )

    return {
        "intent": extraction.intent,
        "target": target,
        "target_type": extraction.target_type,
        "dataset_group": dataset_group,
        "year": extraction.year,
        "rcp": extraction.rcp,
        "variable": extraction.variable,
        "variation": extraction.variation,
        "variation_type": extraction.variation_type,
    }