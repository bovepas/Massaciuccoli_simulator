# -*- coding: utf-8 -*-
"""
Router benchmark 2: the 110 questions from the Massaciuccoli agents comparison workbook.

Run from the application project root:
    python -m tests.test_router_bm_cosin_2

The workbook's intent labels are retained as SOURCE_INTENTS for traceability, but
EXPECTED_TYPES uses the Massaciuccoli Digital Twin's existing task taxonomy.
This script tests routing only; it does not judge final-answer quality or change
production router/orchestrator code.
"""

from collections import Counter, defaultdict
from router.semantic_router import route_question

SHOW_ONLY_ERRORS = True

# Each entry is (question, expected_task_type). The existing task taxonomy is
# intentionally preserved; source workbook categories are in SOURCE_INTENTS.
TESTS = [
    ("Which environmental variables are available in the dataset?", "data"),  # source: Data
    ("Which environmental variables are explicitly included in the dataset?", "data"),  # source: Data
    ("Which environmental stressors are explicitly measured in the dataset?", "data"),  # source: Data
    ("Which variables in the dataset capture the main ecological dynamics of the basin?", "data"),  # source: Data
    ("Which aspects of ecosystem functioning are represented in the dataset?", "data"),  # source: Data
    ("Which ecological variables are represented in the dataset?", "data"),  # source: Data
    ("Which ecological variables are available in the dataset for ecosystem assessment?", "data"),  # source: Data
    ("Which environmental variables are most strongly associated with biodiversity in the Massaciuccoli basin?", "drivers"),  # source: Correlation
    ("How does land-use change affect biodiversity in the Massaciuccoli basin?", "dependency"),  # source: Correlation
    ("How does temperature change affect biodiversity in the Massaciuccoli ecosystem?", "dependency"),  # source: Correlation
    ("How does evapotranspiration change affect biodiversity in the Massaciuccoli basin?", "dependency"),  # source: Correlation
    ("How does tree cover affect biodiversity in the Massaciuccoli basin?", "dependency"),  # source: Correlation
    ("Does temperature directly cause biodiversity loss in the basin?", "dependency"),  # source: Correlation
    ("Does tree cover alone control biodiversity?", "dependency"),  # source: Correlation
    ("Does precipitation directly cause biodiversity loss?", "dependency"),  # source: Correlation
    ("Which environmental variable contributes most to biodiversity change?", "drivers"),  # source: Correlation
    ("What factors drive changes in vegetation productivity?", "drivers"),  # source: Correlation
    ("Which environmental variables are most strongly associated with evapotranspiration change?", "drivers"),  # source: Correlation
    ("Which environmental variables are most strongly associated with precipitation change in the basin?", "drivers"),  # source: Correlation
    ("How does precipitation affect species richness?", "dependency"),  # source: Correlation
    ("What factors drive tree cover dynamics in the basin?", "drivers"),  # source: Correlation
    ("What factors drive biodiversity patterns in the lake ecosystem?", "drivers"),  # source: Correlation
    ("How does tree cover affect species richness?", "dependency"),  # source: Correlation
    ("How does evapotranspiration affect biodiversity?", "dependency"),  # source: Correlation
    ("Which environmental variables contribute most to ecosystem risk under changing climatic conditions?", "importance"),  # source: Importance
    ("How does precipitation change affect ecosystem risk in the Massaciuccoli basin?", "dependency"),  # source: Importance
    ("Does precipitation directly determine ecosystem risk?", "dependency"),  # source: Importance
    ("Does biodiversity alone determine ecosystem risk?", "dependency"),  # source: Importance
    ("Does biodiversity directly determine ecosystem risk?", "dependency"),  # source: Importance
    ("Does temperature alone control ecosystem risk?", "dependency"),  # source: Importance
    ("Which environmental pressures are most relevant for ecosystem risk in the Massaciuccoli basin?", "importance"),  # source: Importance
    ("Which environmental conditions are associated with lower ecosystem risk in the Massaciuccoli basin?", "importance"),  # source: Importance
    ("Which environmental variables contribute most to ecosystem risk in the Massaciuccoli basin?", "importance"),  # source: Importance
    ("How does biodiversity influence ecosystem risk in the Massaciuccoli basin?", "dependency"),  # source: Importance
    ("Which environmental conditions are associated with lower ecosystem risk in the Massaciuccoli basin?", "importance"),  # source: Importance
    ("What factors drive ecosystem risk?", "importance"),  # source: Importance
    ("What are the three environmental variables that most influence ecosystem risk?", "importance"),  # source: Importance
    ("Which climate-related variable has the strongest impact on ecosystem risk?", "importance"),  # source: Importance
    ("How does tree cover influence ecosystem risk?", "dependency"),  # source: Importance
    ("How does temperature affect ecosystem risk in the lake basin?", "dependency"),  # source: Importance
    ("How does evapotranspiration affect ecosystem risk?", "dependency"),  # source: Importance
    ("How does precipitation affect ecosystem risk?", "dependency"),  # source: Importance
    ("Which environmental variables should be prioritized to reduce ecosystem risk under climate change?", "importance"),  # source: Importance
    ("Which variables are most important for ecosystem health?", "importance"),  # source: Importance
    ("How does biodiversity affect ecosystem stability?", "dependency"),  # source: Importance
    ("How does tree cover affect ecosystem stability?", "dependency"),  # source: Importance
    ("How does biodiversity affect ecosystem resilience?", "dependency"),  # source: Importance
    ("Which environmental stressors represented in the dataset are most relevant for ecosystem assessment?", "importance"),  # source: Importance
    ("Assess ecosystem risk under a scenario with increased temperature, reduced precipitation and lower biodiversity.", "assessment"),  # source: Variation
    ("Assess ecosystem risk under a scenario with reduced tree cover, lower biodiversity and decreased precipitation", "assessment"),  # source: Variation
    ("How could increasing temperature affect the Massaciuccoli lake ecosystem?", "dependency"),  # source: Variation
    ("How could reduced precipitation affect ecological conditions in the Massaciuccoli basin?", "dependency"),  # source: Variation
    ("How does ecosystem risk change when grassland cover decreases by 50%?", "delta"),  # source: Variation
    ("What is the ecosystem risk if tree cover increases by 70% across the basin?", "delta"),  # source: Variation
    ("What is the ecosystem risk if temperature increases by 3°C and precipitation decreases by 20%?", "assessment"),  # source: Variation
    ("What is the ecosystem risk if temperature decreases by 1°C but precipitation decreases by 15%?", "assessment"),  # source: Variation
    ("What is the ecosystem risk if evapotranspiration increases substantially?", "delta"),  # source: Variation
    ("What is the ecosystem risk if evapotranspiration increases by 25%?", "delta"),  # source: Variation
    ("What is the ecosystem risk if tree cover decreases substantially?", "delta"),  # source: Variation
    ("What happens to ecosystem risk when temperature increases from 0°C to +3°C?", "delta"),  # source: Variation
    ("What happens to ecosystem risk when precipitation changes from 0% to -20%?", "delta"),  # source: Variation
    ("What happens to ecosystem risk when biodiversity decreases from 100% to 70%?", "delta"),  # source: Variation
    ("What happens to ecosystem risk when tree cover increases from 30% to 70%?", "delta"),  # source: Variation
    ("What happens to ecosystem risk when evapotranspiration increases by 25%?", "delta"),  # source: Variation
    ("How does ecosystem risk change when temperature increases by 1°C?", "delta"),  # source: Variation
    ("How does ecosystem risk change when temperature increases by 2°C?", "delta"),  # source: Variation
    ("How does ecosystem risk change when precipitation decreases by 10%?", "delta"),  # source: Variation
    ("How does ecosystem risk change when precipitation decreases by 30%?", "delta"),  # source: Variation
    ("How does ecosystem risk change when biodiversity decreases by 10%?", "delta"),  # source: Variation
    ("How does ecosystem risk change when biodiversity decreases by 50%?", "delta"),  # source: Variation
    ("How does ecosystem risk change when tree cover decreases by 20%?", "delta"),  # source: Variation
    ("How does ecosystem risk change when tree cover increases by 20%?", "delta"),  # source: Variation
    ("What is the ecosystem risk if biodiversity declines by 30%?", "delta"),  # source: Variation
    ("Assess ecosystem risk under a scenario with increased temperature and reduced tree cover", "assessment"),  # source: Variation
    ("What is the ecosystem risk if temperature increases by 3°C but tree cover also increases significantly?", "assessment"),  # source: Variation
    ("What is the ecosystem risk if temperature increases by 2°C, precipitation decreases by 10%, and tree cover declines by 20%?", "assessment"),  # source: Variation
    ("What is the ecosystem risk if biodiversity declines by 20% and grassland cover is reduced by half?", "assessment"),  # source: Variation
    ("Compare a scenario with lower biodiversity against a scenario with increased temperature in terms of ecosystem risk.", "importance_compare"),  # source: Comparison
    ("Compare increased temperature and reduced tree cover in terms of ecosystem risk", "importance_compare"),  # source: Comparison
    ("Compare ecosystem risk when temperature increases by 2°C versus when precipitation decreases by 10%.", "comparison"),  # source: Comparison
    ("Which scenario produces higher ecosystem risk: biodiversity −30% or tree cover −30%?", "comparison"),  # source: Comparison
    ("Which contributes more to ecosystem risk: biodiversity or tree cover?", "importance_compare"),  # source: Comparison
    ("Which has a stronger effect on ecosystem risk: evapotranspiration increase or precipitation decrease?", "importance_compare"),  # source: Comparison
    ("Which scenario is worse: temperature +3°C or precipitation −20%?", "comparison"),  # source: Comparison
    ("Compare a scenario with increased tree cover (70%) and one with reduced biodiversity (−30%)", "comparison"),  # source: Comparison
    ("Compare a scenario with temperature +2°C and a scenario with temperature +2°C but increased tree cover.", "comparison"),  # source: Comparison
    ("Compare climate stress and biodiversity decline as drivers of ecosystem risk.", "importance_compare"),  # source: Comparison
    ("Compare tree-cover restoration and biodiversity conservation as risk mitigation strategies.", "importance_compare"),  # source: Comparison
    ("Which intervention would be more effective: increasing tree cover or reducing land-use change?", "importance_compare"),  # source: Comparison
    ("Compare hydrological stress and biodiversity stress in terms of ecosystem resilience.", "importance_compare"),  # source: Comparison
    ("Is suitable habitat for Alcedo atthis fragmented or well connected?", "enm"),  # source: ENM
    ("How is habitat connectivity structured for Alcedo atthis?", "enm"),  # source: ENM
    ("Is suitable habitat for Cyprinus carpio fragmented or well connected?", "enm"),  # source: ENM
    ("How is habitat connectivity structured for Cyprinus carpio?", "enm"),  # source: ENM
    ("How reliable is the habitat suitability model for Alcedo atthis?", "enm"),  # source: ENM
    ("What does the AUC value indicate about model performance for Alcedo atthis?", "enm"),  # source: ENM
    ("Can the habitat suitability predictions for Alcedo atthis be considered reliable?", "enm"),  # source: ENM
    ("How reliable is the habitat suitability model for Cyprinus carpio?", "enm"),  # source: ENM
    ("What does the AUC value indicate about model performance for Cyprinus carpio?", "enm"),  # source: ENM
    ("Can the habitat suitability predictions for Cyprinus carpio be considered reliable?", "enm"),  # source: ENM
    ("How widespread is suitable habitat for Alcedo atthis across the basin?", "enm"),  # source: ENM
    ("Does Alcedo atthis occupy a few core habitat areas or many distributed habitats?", "enm"),  # source: ENM
    ("How widespread is suitable habitat for Cyprinus carpio across the basin?", "enm"),  # source: ENM
    ("Does Cyprinus carpio occupy a few core habitat areas or many distributed habitats?", "enm"),  # source: ENM
    ("Is habitat suitability for Alcedo atthis controlled by one dominant environmental driver or multiple drivers?", "enm"),  # source: ENM
    ("Does a single environmental factor dominate habitat suitability for Alcedo atthis?", "enm"),  # source: ENM
    ("Are multiple environmental drivers equally important for Alcedo atthis?", "enm"),  # source: ENM
    ("Is habitat suitability for Cyprinus carpio controlled by one dominant environmental driver or multiple drivers?", "enm"),  # source: ENM
    ("Does a single environmental factor dominate habitat suitability for Cyprinus carpio?", "enm"),  # source: ENM
    ("Are multiple environmental drivers equally important for Cyprinus carpio?", "enm"),  # source: ENM
]

SOURCE_INTENTS = [
    "Data",
    "Data",
    "Data",
    "Data",
    "Data",
    "Data",
    "Data",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Correlation",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Importance",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Variation",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "Comparison",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
    "ENM",
]

def run_tests():
    correct = 0
    total = len(TESTS)
    by_expected = defaultdict(lambda: [0, 0])
    errors = []

    print("\n================ COSINE ROUTER BENCHMARK 2 ================\n")
    print(f"Question set: comparison workbook ({total} questions)")

    for i, (question, expected) in enumerate(TESTS, 1):
        result = route_question(question)
        predicted = result.get("type", "<missing>")
        scores = result.get("scores", {})
        ok = predicted == expected
        by_expected[expected][1] += 1
        if ok:
            correct += 1
            by_expected[expected][0] += 1
        else:
            errors.append((i, question, expected, predicted, scores))

        if SHOW_ONLY_ERRORS and ok:
            continue
        status = "OK" if ok else "ERROR"
        print(f"[{status}] [{i:03d}] source={SOURCE_INTENTS[i-1]}")
        print(f"Q: {question}")
        print(f"EXPECTED:  {expected}")
        print(f"PREDICTED: {predicted}")
        if not ok:
            print("SCORES:")
            for task, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                print(f"  {task:20s} {score:.4f}")
        print("-------------------------------------------")

    print("\n================ SUMMARY ================")
    print(f"Questions: {total}")
    print(f"Routing correct: {correct}/{total}")
    print(f"Accuracy: {correct / total * 100:.2f}%")
    print("\nAccuracy by expected task:")
    for task in sorted(by_expected):
        n_ok, n_total = by_expected[task]
        print(f"  {task:20s} {n_ok:3d}/{n_total:<3d} ({n_ok / n_total * 100:6.2f}%)")
    print("========================================\n")


if __name__ == "__main__":
    run_tests()
