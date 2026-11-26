# -*- coding: utf-8 -*-
"""
Router Benchmark Test Suite
Auto-generated from Complete set.xlsx
"""
import io
import contextlib
from versions.v6_1_main import route_question

# ======================================================
# CONFIG
# ======================================================

SHOW_ONLY_ERRORS = True

# ======================================================
# BENCHMARK TEST SET
# ======================================================

TESTS = [
('Which environmental variables are most strongly associated with biodiversity in the Massaciuccoli basin?', 'drivers'),
('Which environmental variables contribute most to ecosystem risk under changing climatic conditions?', 'importance'),
('How is land-use change affect biodiversity in the Massaciuccoli basin?', 'dependency'),
('How is temperature change affect  biodiversity in the Massaciuccoli ecosystem?', 'dependency'),
('How is evapotranspiration change affect biodiversity in the Massaciuccoli basin?', 'dependency'),
('Assess ecosystem risk under a scenario with increased temperature, reduced precipitation and lower biodiversity.', 'assessment'),
('Compare a scenario with lower biodiversity against a scenario with increased temperature in terms of ecosystem risk.', 'importance_compare'),
('Compare increased temperature and reduced tree cover in terms of ecosystem risk.?', 'importance_compare'),
('Is suitable habitat for Alcedo atthis fragmented or well connected?', 'enm'),
('How is habitat connectivity structured for Alcedo atthis?', 'enm'),
('Is suitable habitat for Cyprinus carpio fragmented or well connected?', 'enm'),
('How is habitat connectivity structured for Cyprinus carpio?', 'enm'),

('Does temperature directly cause biodiversity loss in the basin?', 'dependency'),
('Does precipitation directly determine ecosystem risk?', 'dependency'),
('Does tree cover alone control biodiversity?', 'dependency'),
('Which environmental variables are available in the dataset?', 'data'),
('How reliable is the habitat suitability model for Alcedo atthis?', 'enm'),
('What does the AUC value indicate about model performance for Alcedo atthis?', 'enm'),
('Can the habitat suitability predictions for Alcedo atthis be considered reliable?', 'enm'),
('How reliable is the habitat suitability model for Cyprinus carpio?', 'enm'),
('What does the AUC value indicate about model performance for Cyprinus carpio?', 'enm'),
('Can the habitat suitability predictions for Cyprinus carpio be considered reliable?', 'enm'),

('How could increasing temperature affect the Massaciuccoli lake ecosystem?', 'dependency'),
('How could reduced precipitation affect ecological conditions in the Massaciuccoli basin?', 'dependency'),
('What are the main drivers of ecosystem risk in the Massaciuccoli basin?', 'importance'),
('Which environmental conditions are associated with lower ecosystem risk in the Massaciuccoli basin?', 'importance'),
('How does ecosystem risk change when grassland cover decreases by 50%?', 'delta'),
('What is the ecosystem risk if tree cover increases to 70% across the basin?', 'delta'),
('Which environmental stressors are explicitly measured in the dataset?', 'data'),
('Which variables in the dataset capture the main ecological dynamics of the basin?', 'data'),
('How widespread is suitable habitat for Alcedo atthis across the basin?', 'enm'),
('Does Alcedo atthis occupy a few core habitat areas or many distributed habitats?', 'enm'),
('How widespread is suitable habitat for Cyprinus carpio across the basin?', 'enm'),
('Does Cyprinus carpio occupy a few core habitat areas or many distributed habitats?', 'enm'),

('Which environmental variable contributes most to biodiversity change?', 'drivers'),
('What factors drive ecosystem risk?', 'importance'),
('What are the three environmental variables that most influence ecosystem risk?', 'importance'),
('Which climate-related variable has the strongest impact on ecosystem risk?', 'importance'),
('How does tree cover influence ecosystem risk?', 'dependency'),
('What is the ecosystem risk if temperature increases by 3°C and precipitation decreases by 20%?', 'assessment'),
('What is the ecosystem risk if temperature decreases by 1°C but precipitation decreases by 15%?', 'assessment'),
('Compare ecosystem risk when temperature increases by 2°C versus when precipitation decreases by 10%.', 'comparison'),
('Which scenario produces higher ecosystem risk: biodiversity -30% or tree cover -30%?', 'comparison'),
('Which contributes more to ecosystem risk: biodiversity or tree cover?', 'importance_compare'),
('Which has a stronger effect on ecosystem risk: evapotranspiration increase or precipitation decrease?', 'importance_compare'),
('What is the ecosystem risk if evapotranspiration increases substantially?', 'delta'),
('What is the ecosystem risk if evapotranspiration increases by 25%?', 'delta'),
('What is the ecosystem risk if tree cover decreases substantially?', 'delta'),
('What happens to ecosystem risk when temperature increases from 0°C to +3°C?', 'delta'),
('What happens to ecosystem risk when precipitation changes from 0% to -20%?', 'delta'),
('What happens to ecosystem risk when biodiversity decreases from 100% to 70%?', 'delta'),
('What happens to ecosystem risk when tree cover increases from 30% to 70%?', 'delta'),
('What happens to ecosystem risk when evapotranspiration increases by 25%?', 'delta'),
('How does ecosystem risk change when temperature increases by 1°C?', 'delta'),
('How does ecosystem risk change when temperature increases by 2°C?', 'delta'),
('How does ecosystem risk change when precipitation decreases by 10%?', 'delta'),
('How does ecosystem risk change when precipitation decreases by 30%?', 'delta'),
('How does ecosystem risk change when biodiversity decreases by 10%?', 'delta'),
('How does ecosystem risk change when biodiversity decreases by 50%?', 'delta'),
('How does ecosystem risk change when tree cover decreases by 20%?', 'delta'),
('How does ecosystem risk change when tree cover increases by 20%?', 'delta'),
('What is the ecosystem risk if biodiversity declines by 30%?', 'delta'),

('What factors drive changes in vegetation productivity?', 'drivers'),
('Which environmental variables are most strongly associated with evapotranspiration change?', 'drivers'),
('Which environmental variables are most strongly associated with precipitation change in the basin?', 'drivers'),
('How does temperature affect ecosystem risk in the lake basin?', 'dependency'),
('How does evapotranspiration affect ecosystem risk?', 'dependency'),
('How does precipitation affect species richness?', 'dependency'),
('Which ecological variables are represented in the dataset?', 'data'),
('Which aspects of ecosystem functioning are represented in the dataset?', 'data'),

('What factors drive species richness?', 'drivers'),
('Which environmental variables are most important for preserving biodiversity?', 'drivers'),
('Which environmental variables should be prioritized to reduce ecosystem risk under climate change?', 'importance'),
('Which variables are most important for ecosystem health?', 'importance'),
('How does biodiversity affect ecosystem stability?', 'dependency'),
('How does tree cover affect ecosystem stability?', 'dependency'),
('How does biodiversity affect ecosystem resilience?', 'dependency'),
('What is the ecosystem risk if temperature increases by 3°C but tree cover also increases significantly?', 'assessment'),
('What is the ecosystem risk if temperature increases by 2°C, precipitation decreases by 10%, and tree cover declines by 20%?', 'assessment'),
('What is the ecosystem risk if biodiversity declines by 20% and grassland cover is reduced by half?', 'assessment'),
('Which scenario is worse: temperature +3°C or precipitation −20%?', 'comparison'),
('Compare a scenario with increased tree cover (70%) and one with reduced biodiversity (−30%).', 'comparison'),
('Compare a scenario with temperature +2°C and a scenario with temperature +2°C but increased tree cover.', 'comparison'),
('Compare climate stress and biodiversity decline as drivers of ecosystem risk.', 'importance_compare'),
('Compare tree-cover restoration and biodiversity conservation as risk mitigation strategies.', 'importance_compare'),
('Which intervention would be more effective: increasing tree cover or reducing land-use change?', 'importance_compare'),
('Compare hydrological stress and biodiversity stress in terms of ecosystem resilience.', 'importance_compare'),
('Which environmental stressors represented in the dataset are most relevant for ecosystem assessment?', 'data'),
('Is habitat suitability for Alcedo atthis controlled by one dominant environmental driver or multiple drivers?', 'enm'),
('Does a single environmental factor dominate habitat suitability for Alcedo atthis?', 'enm'),
('Are multiple environmental drivers equally important for Alcedo atthis?', 'enm'),
('Is habitat suitability for Cyprinus carpio controlled by one dominant environmental driver or multiple drivers?', 'enm'),
('Does a single environmental factor dominate habitat suitability for Cyprinus carpio?', 'enm'),
('Are multiple environmental drivers equally important for Cyprinus carpio?', 'enm'),

('How does tree cover affect biodiversity in the Massaciuccoli basin?', 'dependency'),
('How does precipitation change affect ecosystem risk in the Massaciuccoli basin?', 'dependency'),
('Assess ecosystem risk under a scenario with reduced tree cover, lower biodiversity and decreased precipitation.', 'assessment'),

('Does biodiversity alone determine ecosystem risk?', 'dependency'),
('Does precipitation directly cause biodiversity loss?', 'dependency'),
('Does temperature directly determine ecosystem risk?', 'dependency'),
('Which environmental variables are explicitly included in the dataset?', 'data'),
('Does temperature alone control ecosystem risk?', 'dependency'),

('Which environmental variables contribute most to ecosystem risk in the Massaciuccoli basin?', 'importance'),
('How does biodiversity influence ecosystem risk in the Massaciuccoli basin?', 'dependency'),
('Which environmental conditions are associated with lower ecosystem risk in the Massaciuccoli basin?', 'importance'),

('What factors drive tree cover dynamics in the basin?', 'drivers'),
('What factors drive biodiversity patterns in the lake ecosystem?', 'drivers'),
('How does tree cover affect species richness?', 'dependency'),
('How does precipitation affect ecosystem risk?', 'dependency'),
('How does evapotranspiration affect biodiversity?', 'dependency'),
('Assess ecosystem risk under a scenario with increased temperature and reduced tree cover.', 'assessment'),
('Which ecological variables are available in the dataset for ecosystem assessment?', 'data'),


]

# ======================================================
# RUN TESTS
# ======================================================

def run_tests():

    correct = 0
    total = len(TESTS)

    print("\n================ ROUTER BENCHMARK TESTS ================\n")

    for i, (question, expected) in enumerate(TESTS, 1):

        if SHOW_ONLY_ERRORS:

            with contextlib.redirect_stdout(io.StringIO()):
                result = route_question(question)

        else:

            result = route_question(question)

        predicted = result["type"]

        ok = predicted == expected

        if ok:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        if SHOW_ONLY_ERRORS and ok:
            continue

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


if __name__ == "__main__":
    run_tests()
