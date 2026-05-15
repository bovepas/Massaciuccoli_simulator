# tasks/task_data.py

from tools.live_data_loader import load_live_data, safe_get
from utils.data_parser import parse_data_request


# ======================================================
# 🔥 LABEL USER-FRIENDLY
# ======================================================

VARIABLE_LABELS = {
    "temperature change": "average temperature change (°C)",
    "water from rain": "precipitation change (%)",
    "evaporation change": "evaporation change (%)",
    "tree": "tree cover (%)",
    "grassland": "grassland area (%)",
    "species richness": "species richness"
}


# ======================================================
# MAIN
# ======================================================

def handle_data(question):

    print("\n========== DATA TASK START ==========")

    try:
        # ======================================================
        # 🔥 STEP 1: LOAD LIVE DATA
        # ======================================================
        print("[DATA] Loading live data...")
        row = load_live_data()

        # ======================================================
        # 🔥 STEP 2: PARSE USER REQUEST (CENTRALIZED)
        # ======================================================
        parsed = parse_data_request(question)
        variable = parsed.get("variable")

        # ======================================================
        # 🔥 STEP 3: SINGLE VARIABLE
        # ======================================================
        if variable:

            value = safe_get(row, variable)

            try:
                value = float(value)
            except:
                pass

            label = VARIABLE_LABELS.get(variable, variable)

            return {
                "summary": "Latest environmental data",
                "data": {
                    variable: value
                },
                "drivers": [],
                "interpretation": f"The latest {label} is {value}."
            }

        # ======================================================
        # 🔥 STEP 4: FULL SNAPSHOT
        # ======================================================
        data = {
            "temperature": safe_get(row, "temperature change"),
            "precipitation": safe_get(row, "water from rain"),
            "evaporation": safe_get(row, "evaporation change"),
            "tree_cover": safe_get(row, "tree"),
            "species": safe_get(row, "species richness")
        }

        for k, v in data.items():
            try:
                data[k] = float(v)
            except:
                pass

        return {
            "summary": "Latest environmental data",
            "data": data,
            "drivers": [],
            "interpretation": "Here is the latest environmental snapshot of the lake system."
        }

    except Exception as e:
        print("[DATA ERROR]", e)

        return {
            "summary": "Data retrieval failed",
            "data": {},
            "drivers": [],
            "interpretation": "Could not retrieve the latest environmental data."
        }