# -*- coding: utf-8 -*-
"""
Router Test Suite — Massaciuccoli Digital Twin
Run all routing tests automatically
"""

from versions.v6_1_main import route_question


# ======================================================
# TEST SET
# ======================================================

TESTS = [

    # ======================
    # 🆕 DATA
    # ======================
    ("Get temperature data", "data"),
    ("Retrieve precipitation values", "data"),
    ("Show biodiversity data", "data"),
    ("What are the latest temperature measurements?", "data"),
    ("Give me the current precipitation values", "data"),
    ("Show ecosystem productivity data", "data"),
    ("Retrieve evapotranspiration time series", "data"),
    ("Get the latest biodiversity numbers", "data"),

    # ======================
    # ASSESSMENT
    # ======================
    ("What is the ecosystem risk with temperature increase of 2°C and precipitation decrease of 20%?", "assessment"),
    ("Estimate ecosystem risk given evapotranspiration increase of 15% and biodiversity equal to 180 species.", "assessment"),
    ("What is the current state of the ecosystem?", "assessment"),
    ("Describe the current condition of the lake ecosystem.", "assessment"),
    ("If temperature increases by +3°C but tree cover also increases significantly, how do these combined effects influence ecosystem risk?", "assessment"),
    ("what is the ecosystem risk with temperature +2°C", "assessment"),
    ("estimate risk with precipitation -20%", "assessment"),
    ("How do changes in land use and tree cover interact to influence ecosystem risk?", "assessment"),
    ("describe the current state of the ecosystem", "assessment"),
    ("If the climate becomes warmer and drier, how does ecosystem risk change?", "assessment"),

    # ======================
    # DEPENDENCY
    # ======================
    ("How does temperature affect biodiversity?", "dependency"),
    ("How does grassland presence affect tree cover?", "dependency"),
    ("What is the effect of precipitation on biodiversity?", "dependency"),
    ("If temperature increases, how does tree cover change?", "dependency"),
    ("How does evapotranspiration influence grassland presence?", "dependency"),
    ("If precipitation decreases by 10, how does biodiversity change?", "dependency"),
    ("Does precipitation change affect ecosystem productivity?", "dependency"),
    ("How does biodiversity change if temperature increases by 2°C?", "dependency"),
    ("What is the effect of increasing evapotranspiration?", "dependency"),

    # ======================
    # DELTA
    # ======================
    ("How does ecosystem risk change from 0°C to 20°C temperature increase?", "delta"),
    ("What is the effect on ecosystem risk when precipitation goes from -20% to +30%?", "delta"),
    ("how does risk change from 0 to 20 temperature", "delta"),
    ("what happens from -10 to +30 precipitation", "delta"),
    ("change in risk from 5 to 15 evapotranspiration", "delta"),
    ("What is the expected change in ecosystem risk if tree cover density decreases from 60% to 30%, while all other environmental variables remain constant?", "delta"),
    ("How does the ecosystem risk change if precipitation decreases from -10% to -40%, keeping all other variables constant?", "delta"),
    ("What happens if temperature increases by 1?", "delta"),
    ("What happens if precipitation decreases by 10%?", "delta"),
    ("What happens to ecosystem risk if temperature increases by 2?", "delta"),

    # ======================
    # COMPARISON
    # ======================
    ("which scenario is riskier: high vs low biodiversity", "comparison"),
    ("Compare two scenarios: temperature +1°C and precipitation -10% versus temperature +3°C and precipitation -30%. Which leads to higher ecosystem risk?", "comparison"),
    ("Which scenario is riskier: temperature increase of 1°C or temperature increase of 4°C?", "comparison"),

    # ======================
    # IMPORTANCE
    # ======================
    ("What are the main factors driving the ecosystem risk in this scenario.", "importance"),
    ("Explain the main factors driving the ecosystem risk in this scenario. List the top 3 most influential variables.", "importance"),
    ("What are the top 3 most influential variables affecting ecosystem risk under baseline conditions?", "importance"),
    ("What are the main drivers if temperature increases by 2?", "importance"),
    ("Which variables are most influential if precipitation decreases by 20%?", "importance"),
    ("Which variables reduce ecosystem risk the most?", "importance"),
    ("Which factors increase ecosystem risk the most?", "importance"),
    ("What drives ecosystem risk the most?", "importance"),
    ("What variables are most important for ecosystem risk?", "importance"),
    ("Which factors increase ecosystem risk?", "importance"),

    # ======================
    # DRIVERS
    # ======================
    ("Which are the factors whose change may drive a temperature increase?", "drivers"),
    ("Top 3 drivers of biodiversity", "drivers"),
    ("Which factors drive biodiversity loss?", "drivers"),
    ("What drives precipitation change?", "drivers"),

    # ======================
    # ENM
    # ======================
    ("Cyprinus carpio habitat suitability", "enm"),
    ("What is the predicted habitat suitability of Cyprinus carpio in the study area?", "enm"),
    ("What is the habitat suitability of fish species in the area given temperature increase of 2°C?", "enm"),
]


# ======================================================
# RUN TESTS
# ======================================================

def run_tests():

    correct = 0
    total = len(TESTS)

    print("\n================ ROUTER TESTS ================\n")

    for i, (question, expected) in enumerate(TESTS, 1):

        result = route_question(question)
        predicted = result["type"]

        ok = predicted == expected

        if ok:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"{status} [{i}]")
        print(f"Q: {question}")
        print(f"EXPECTED:  {expected}")
        print(f"PREDICTED: {predicted}")
        print("-------------------------------------------")

    accuracy = correct / total * 100

    print("\n============================================")
    print(f"RESULT: {correct}/{total} correct")
    print(f"ACCURACY: {accuracy:.2f}%")
    print("============================================\n")


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    run_tests()