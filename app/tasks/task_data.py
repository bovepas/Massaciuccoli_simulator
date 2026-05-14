# tasks/task_data.py

from tools.live_data_loader import load_live_data, safe_get


# ======================================================
# 🔥 LIGHT DATA PARSER
# ======================================================

def detect_requested_variable(question: str):

    q = question.lower()

    if "temperature" in q:
        return "temperature change"

    if "precipitation" in q or "rain" in q:
        return "water from rain"

    if "evaporation" in q:
        return "evaporation change"

    if "tree" in q:
        return "tree"

    if "grass" in q:
        return "grassland"

    if "species" in q or "biodiversity" in q:
        return "species richness"

    return None


# ======================================================
# MAIN
# ======================================================

def handle_data(question):

    print("\n========== DATA TASK START ==========")

    try:
        # ======================================================
        # 🔥 STEP 1: CARICA DATI LIVE
        # ======================================================
        print("[DATA] Loading live data...")
        row = load_live_data()

        # ======================================================
        # 🔥 STEP 2: PARSE USER REQUEST
        # ======================================================
        variable = detect_requested_variable(question)

        # ======================================================
        # 🔥 STEP 3: SINGLE VARIABLE
        # ======================================================
        if variable:

            value = safe_get(row, variable)

            try:
                value = float(value)
            except:
                pass

            return {
                "summary": "Latest environmental data",
                "data": {
                    variable: value
                },
                "drivers": [],
                "interpretation": f"The latest value for {variable} is {value}."
            }

        # ======================================================
        # 🔥 STEP 4: FULL SNAPSHOT (fallback)
        # ======================================================
        data = {
            "temperature": safe_get(row, "temperature change"),
            "precipitation": safe_get(row, "water from rain"),
            "evaporation": safe_get(row, "evaporation change"),
            "tree_cover": safe_get(row, "tree"),
            "species": safe_get(row, "species richness")
        }

        # cast sicuro
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