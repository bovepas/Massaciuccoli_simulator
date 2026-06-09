# -*- coding: utf-8 -*-
"""
Router Benchmark Test Suite
Auto-generated from Complete set.xlsx
"""

from versions.v6_1_main import route_question

# ======================================================
# BENCHMARK TEST SET
# ======================================================

TESTS = [
    ('What factors drive biodiversity loss in the lake ecosystem?', 'drivers'),
    ('What factors drive climate-related stress in the lake ecosystem?', 'drivers'),
    ('What factors drive changes in vegetation productivity?', 'drivers'),
    ('What factors drive evapotranspiration dynamics?', 'drivers'),
    ('What factors drive land use in the basin?', 'drivers'),
    ('What factors drive species richness?', 'drivers'),
    ('What factors drive changes in precipitation in the lake?', 'drivers'),
    ('Which environmental variable contributes most to biodiversity change?', 'drivers'),
    ('Which environmental variables are most important for preserving biodiversity?', 'drivers'),

    ('What factors drive ecosystem risk?', 'importance'), 
    ('What are the three environmental variables that most influence ecosystem risk?', 'importance'),
    ('Which climate-related variable has the strongest impact on ecosystem risk?', 'importance'),
    ('Which environmental variables should be prioritized to reduce ecosystem risk under climate change?', 'importance'),
    ('Which variables are most important for ecosystem health?', 'importance'),

   
    ('How does temperature affect precipitation in the lake basin?', 'dependency'),
    ('What is the effect of evapotranspiration on water availability?', 'dependency'),
    ('How does land-use change affect biodiversity?', 'dependency'),
    ('How does biodiversity affect ecosystem stability?', 'dependency'),
    ('How does temperature influence biodiversity in the ecosystem?', 'dependency'),
    ('How does tree cover influence ecosystem risk?', 'dependency'),
    ('How does precipitation affect species richness?', 'dependency'),
    ('How does evapotranspiration influence biodiversity?', 'dependency'),
    ('How does tree cover affect ecosystem stability?', 'dependency'),
    ('How does biodiversity affect ecosystem resilience?', 'dependency'),
    ('Does temperature directly cause biodiversity loss in the basin?', 'dependency'),
    ('Does precipitation directly determine ecosystem risk?', 'dependency'),
    ('Does tree cover alone control biodiversity?', 'dependency'),
    ('How could increasing temperature affect this lake ecosystem?', 'dependency'),
    ('How could reduced precipitation affect ecological conditions in the basin?', 'dependency'),
    
    ('What is the ecosystem risk if temperature increases by 3°C and precipitation decreases by 20%?', 'assessment'),
    ('What is the ecosystem risk if temperature increases by 3°C but tree cover also increases significantly?', 'assessment'),
    ('What is the ecosystem risk if temperature increases by 2°C, precipitation decreases by 10%, and tree cover declines by 20%?', 'assessment'),
    ('What is the ecosystem risk if biodiversity declines by 20% and grassland cover is reduced by half?', 'assessment'),
    ('What is the ecosystem risk if temperature decreases by 1°C but precipitation decreases by 15%?', 'assessment'),
    ('What are the main environmental vulnerabilities of this lake ecosystem?', 'assessment'),
    ('Which environmental pressures are most relevant in this basin?', 'assessment'),
    ('What environmental changes pose the greatest threat to the future of the basin?', 'assessment'),
    ('What environmental characteristics define a healthy lake ecosystem in this basin?', 'assessment'),
    
    ('Which scenario is worse: temperature +3°C or precipitation −20%?', 'comparison'),
    ('Compare ecosystem risk when temperature increases by 2°C versus when precipitation decreases by 10%.', 'comparison'),
    ('Which scenario produces higher ecosystem risk: biodiversity −30% or tree cover −30%?', 'comparison'),
    ('Compare a scenario with increased tree cover (70%) and one with reduced biodiversity (−30%).', 'comparison'),
    ('Compare a scenario with temperature +2°C and a scenario with temperature +2°C but increased tree cover.', 'comparison'),
    ('Which contributes more to ecosystem risk: biodiversity or tree cover?', 'comparison'),
    ('Which has a stronger effect on ecosystem risk: evapotranspiration increase or precipitation decrease?', 'comparison'),
    ('Compare biodiversity loss and climate stress in terms of their impact on the basin.', 'comparison'),
    ('Compare climate stress and biodiversity decline as drivers of ecosystem risk.', 'comparison'),
    ('Compare tree-cover restoration and biodiversity conservation as risk mitigation strategies.', 'comparison'),
    ('Which intervention would be more effective: increasing tree cover or reducing land-use change?', 'comparison'),
    ('Which environmental pressure has the greater ecological impact: warming or habitat degradation?', 'comparison'),
    ('Compare hydrological stress and biodiversity stress in terms of ecosystem resilience.', 'comparison'),

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
    ('How does ecosystem risk change when vegetation productivity decreases substantially?', 'delta'),
    ('How does ecosystem risk change when grassland cover decreases by 50%?', 'delta'),
    ('What is the ecosystem risk if biodiversity declines by 30%?', 'delta'),
    ('What is the ecosystem risk if tree cover increases to 70% across the basin?', 'delta'),


    ('Which environmental variables are available in the dataset?', 'data'),
    ('Which aspects of ecosystem functioning are represented in the dataset?', 'data'),
    ('What important ecological variables are not represented in the dataset?', 'data'),
    ('Which environmental stressors are explicitly measured in the dataset?', 'data'),
    ('Which environmental stressors represented in the dataset are most relevant for ecosystem assessment?', 'data'),
    ('Which variables in the dataset capture the main ecological dynamics of the basin?', 'data'),
   
    # ('What environmental conditions are most suitable for Species X?', 'enm'),
    # ('Which environmental variables most influence habitat suitability for Species X?', 'enm'),
    # ('How would a 2°C temperature increase affect habitat suitability for Species X?', 'enm'),
    # ('How would a 20% reduction in precipitation affect habitat suitability for Species X?', 'enm'),
    # ('How would increased evapotranspiration affect habitat suitability for Species X?', 'enm'),
    # ('Which environmental factor is most limiting for Species X?', 'enm'),
    # ('Which environmental factor most favors Species X?', 'enm'),
    # ('Would increased tree cover improve habitat suitability for Species X?', 'enm'),
    # ('Would biodiversity decline affect habitat suitability for Species X?', 'enm'),
    # ('Which climate-related variable has the strongest influence on Species X?', 'enm'),
 

]

# ======================================================
# RUN TESTS
# ======================================================

def run_tests():

    correct = 0
    total = len(TESTS)

    print("\n================ ROUTER BENCHMARK TESTS ================\n")

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


if __name__ == "__main__":
    run_tests()
