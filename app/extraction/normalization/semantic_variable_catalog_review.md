# Massaciuccoli Digital Twin — catalogo semantico delle variabili

## Base scientifica e criterio di classificazione

Catalogo ricavato dalla Tabella 1 e dalle sezioni 3.1.2–3.1.3 dell’articolo allegato, *A multi-model generalisable ecosystem risk assessment methodology for the Massaciuccoli Lake basin wetland*, di Gian Luca Vannini e Gianpaolo Coro.

**Distinzione essenziale:** l’articolo chiama collettivamente tutte le 12 feature “stressor variables”, ma assegna a ciascuna uno di due ruoli ecologici: `harmful_force` (8 variabili) oppure `fragile_condition` (4 indicatori). Gli indicatori di condizioni fragili non vanno descritti automaticamente come pressioni dannose o cause di degrado.

La tassonomia e i tag sono fondati sull’articolo. La corrispondenza fra nomi Atlas e nomi tecnici del CSV applicativo va ancora verificata nelle voci marcate con uno stato provvisorio.

## Riepilogo

| Atlas ID | Feature canonica nel modello | Ruolo | Tag | Unità | Stato della corrispondenza |
|---:|---|---|---|---|---|
| 3 | Density change in land imperviousness | `harmful_force` | stressor_variable, harmful_force, anthropogenic_pressure, land_use, imperviousness, land_change | % | `probable_match_requires_encoding_check` |
| 9 | Density of tree cover | `fragile_condition` | stressor_variable, fragile_condition, ecosystem_state, vegetation, habitat, tree_cover, forest | % | `strong_match` |
| 10 | Change in tree cover density in the past decade | `harmful_force` | stressor_variable, harmful_force, habitat_degradation, vegetation, tree_cover, forest, land_change | classes | `probable_alias_requires_encoding_check` |
| 11 | Presence of grassland | `fragile_condition` | stressor_variable, fragile_condition, ecosystem_state, vegetation, grassland, habitat | classes | `strong_match` |
| 12 | Change in grassland presence in the past decade | `harmful_force` | stressor_variable, harmful_force, habitat_degradation, vegetation, grassland, habitat, land_change | classes | `probable_alias_requires_encoding_check` |
| 17 | Land use and cover | `harmful_force` | stressor_variable, harmful_force, anthropogenic_pressure, land_use, habitat_degradation, infrastructure, pollution | classes | `provisional_mapping_requires_data_dictionary` |
| 40 | Index of total productivity by plant phenology | `fragile_condition` | stressor_variable, fragile_condition, ecosystem_state, vegetation, productivity, phenology, ecosystem_function | index/range as stored in source | `strong_match_check_units` |
| 57 | Change in average temperature compared to a recent past | `harmful_force` | stressor_variable, harmful_force, climate, temperature, climate_change, thermal_stress | °C | `strong_match_check_reference_period` |
| 58 | Relative change in the potential evapotranspiration compared to a recent past | `harmful_force` | stressor_variable, harmful_force, climate, hydrology, evapotranspiration, aridity, water_balance | % | `strong_concept_match_check_sign` |
| 59 | Cumulative change in precipitation compared to a recent past | `harmful_force` | stressor_variable, harmful_force, climate, hydrology, precipitation, aridity, water_balance | % | `strong_concept_match_check_sign` |
| 65 | Number of species potentially living in the cell | `fragile_condition` | stressor_variable, fragile_condition, ecosystem_state, biodiversity, species_richness, ecological_indicator | number of species / index as defined by source | `strong_concept_match` |
| 147 | Change in land use and cover in the past decade | `harmful_force` | stressor_variable, harmful_force, anthropogenic_pressure, land_use, land_change, anthropisation | classes | `probable_alias_requires_encoding_check` |

## Schede delle variabili

### Atlas ID 3 — Density change in land imperviousness

- **Nome nell’articolo/Atlas:** Land imperviousness density increase
- **Descrizione:** Change in degree of land imperviousness, from -100% to +100%.
- **Tipo:** numeric
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** %
- **Codifica/trasformazione descritta nell’articolo:** Stable non-built-up cells -> 100%; unclassifiable/outside area -> NA; other values -> as is.
- **Alias:** land imperviousness, imperviousness increase, soil sealing, land sealing
- **Tag:** stressor_variable, harmful_force, anthropogenic_pressure, land_use, imperviousness, land_change
- **Stato mappatura:** `probable_match_requires_encoding_check`
- **Nota da verificare:** The concept matches Atlas ID 3, but the article's mapping of stable non-built-up cells to 100% is non-intuitive. Verify actual CSV semantics and preprocessing before interpreting sign or magnitude.

### Atlas ID 9 — Density of tree cover

- **Nome nell’articolo/Atlas:** Tree cover density
- **Descrizione:** Level of tree-cover density, from 0% to 100%.
- **Tipo:** numeric
- **Ruolo ecologico:** `fragile_condition`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** %
- **Codifica/trasformazione descritta nell’articolo:** As is.
- **Alias:** tree cover, forest cover, tree density, forest density
- **Tag:** stressor_variable, fragile_condition, ecosystem_state, vegetation, habitat, tree_cover, forest
- **Stato mappatura:** `strong_match`
- **Nota da verificare:** The application feature and Atlas name correspond directly. It is an ecosystem-state/fragile-condition indicator, not automatically a harmful force.

### Atlas ID 10 — Change in tree cover density in the past decade

- **Nome nell’articolo/Atlas:** Tree cover density decrease
- **Descrizione:** Changes in tree-cover density across thematic classes: unchanged areas without tree cover, new tree cover, tree-cover loss, and unchanged areas with tree cover.
- **Tipo:** categorical
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `inverse`
- **Unità:** classes
- **Codifica/trasformazione descritta nell’articolo:** Unchanged without tree cover -> 0; new tree cover -> -1; tree-cover loss -> 1; unchanged with tree cover -> 0; other values -> 0.
- **Alias:** tree cover change, tree-cover loss, tree cover decrease, forest cover loss, change in forest cover
- **Tag:** stressor_variable, harmful_force, habitat_degradation, vegetation, tree_cover, forest, land_change
- **Stato mappatura:** `probable_alias_requires_encoding_check`
- **Nota da verificare:** Likely corresponds to Atlas ID 10, but the Atlas feature specifically encodes a decrease/loss indicator while the application name is broader. Verify the CSV category codes.

### Atlas ID 11 — Presence of grassland

- **Nome nell’articolo/Atlas:** Grassland cover
- **Descrizione:** Classification of grassland cover with two thematic classes: grassland and non-grassland.
- **Tipo:** categorical
- **Ruolo ecologico:** `fragile_condition`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** classes
- **Codifica/trasformazione descritta nell’articolo:** Grassland -> 1; non-grassland -> 0.
- **Alias:** grassland, grassland habitat, grassland cover, presence of grassland habitat
- **Tag:** stressor_variable, fragile_condition, ecosystem_state, vegetation, grassland, habitat
- **Stato mappatura:** `strong_match`
- **Nota da verificare:** The concept matches Atlas ID 11. This is a presence/class indicator, not a percentage of grassland area.

### Atlas ID 12 — Change in grassland presence in the past decade

- **Nome nell’articolo/Atlas:** Grassland cover decrease
- **Descrizione:** Changes in grassland cover across thematic classes, including grassland gain/loss, unchanged areas, and unverified gain/loss.
- **Tipo:** categorical
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `inverse`
- **Unità:** classes
- **Codifica/trasformazione descritta nell’articolo:** Unchanged non-grassland -> 0; grassland gain -> -1; loss -> 1; unchanged grassland -> 0; unverified gain -> -1; unverified loss -> 1; other values -> 0.
- **Alias:** grassland change, grassland loss, grassland decrease, grassland gain, change in grassland cover
- **Tag:** stressor_variable, harmful_force, habitat_degradation, vegetation, grassland, habitat, land_change
- **Stato mappatura:** `probable_alias_requires_encoding_check`
- **Nota da verificare:** Likely corresponds to Atlas ID 12. Verify whether the current CSV stores Atlas classes, a simplified binary feature, or another encoding.

### Atlas ID 17 — Land use and cover

- **Nome nell’articolo/Atlas:** Land use and cover (Natura 2000) hazard area
- **Descrizione:** Land use/cover in Natura 2000 sites, restricted to selected classes potentially harmful to natural ecosystems: industrial, commercial/military, mineral extraction, dumps/construction sites, and highly modified watercourses/canals.
- **Tipo:** categorical
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** classes
- **Codifica/trasformazione descritta nell’articolo:** Selected hazard classes -> 1; other classes -> 0.
- **Alias:** land use, land cover, land use/land cover, Natura 2000 hazard areas, land use hazard area
- **Tag:** stressor_variable, harmful_force, anthropogenic_pressure, land_use, habitat_degradation, infrastructure, pollution
- **Stato mappatura:** `provisional_mapping_requires_data_dictionary`
- **Nota da verificare:** The application's label is broad; Atlas ID 17 specifically represents selected hazard classes in Natura 2000 sites. Confirm the CSV description and categories before treating this as an exact match.

### Atlas ID 40 — Index of total productivity by plant phenology

- **Nome nell’articolo/Atlas:** Plant productivity
- **Descrizione:** Sum of daily vegetation phenological-index values during the growing season; an annual estimate of accumulated plant biomass and ecosystem productivity.
- **Tipo:** numeric
- **Ruolo ecologico:** `fragile_condition`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** index/range as stored in source
- **Codifica/trasformazione descritta nell’articolo:** As is.
- **Alias:** plant productivity, vegetation productivity, phenology index, ecosystem productivity, vegetation growth
- **Tag:** stressor_variable, fragile_condition, ecosystem_state, vegetation, productivity, phenology, ecosystem_function
- **Stato mappatura:** `strong_match_check_units`
- **Nota da verificare:** The concept matches Atlas ID 40. Confirm the unit/scale from the CSV metadata; do not automatically describe this index as a percentage.

### Atlas ID 57 — Change in average temperature compared to a recent past

- **Nome nell’articolo/Atlas:** Temperature increase
- **Descrizione:** Absolute change in air temperature (approximately 2 m above ground) relative to the 1971–2010 average.
- **Tipo:** numeric
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** °C
- **Codifica/trasformazione descritta nell’articolo:** As is.
- **Alias:** temperature, temperature change, temperature increase, warming, air temperature change
- **Tag:** stressor_variable, harmful_force, climate, temperature, climate_change, thermal_stress
- **Stato mappatura:** `strong_match_check_reference_period`
- **Nota da verificare:** The concept matches Atlas ID 57. Verify that the application's CSV uses the same 1971–2010 reference period.

### Atlas ID 58 — Relative change in the potential evapotranspiration compared to a recent past

- **Nome nell’articolo/Atlas:** Potential evapotranspiration decrease
- **Descrizione:** Relative change in potential evapotranspiration compared with the average across 1971–2010.
- **Tipo:** numeric
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `inverse`
- **Unità:** %
- **Codifica/trasformazione descritta nell’articolo:** As is, with the stressor defined inversely in the article's taxonomy.
- **Alias:** evapotranspiration, potential evapotranspiration, PET, evaporation change, aridity indicator
- **Tag:** stressor_variable, harmful_force, climate, hydrology, evapotranspiration, aridity, water_balance
- **Stato mappatura:** `strong_concept_match_check_sign`
- **Nota da verificare:** The concepts match, but the application's feature name does not explicitly say 'decrease'. Verify the data sign convention and transformation; do not infer direction from the name alone.

### Atlas ID 59 — Cumulative change in precipitation compared to a recent past

- **Nome nell’articolo/Atlas:** Precipitation decrease
- **Descrizione:** Relative change in precipitation per unit area compared with the average across 1971–2010.
- **Tipo:** numeric
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `inverse`
- **Unità:** %
- **Codifica/trasformazione descritta nell’articolo:** As is, with the stressor defined inversely in the article's taxonomy.
- **Alias:** precipitation, rain, rainfall, precipitation decrease, rainfall change
- **Tag:** stressor_variable, harmful_force, climate, hydrology, precipitation, aridity, water_balance
- **Stato mappatura:** `strong_concept_match_check_sign`
- **Nota da verificare:** The concepts match, but the application's feature name does not explicitly say 'decrease'. Verify the data sign convention and transformation; do not infer direction from the name alone.

### Atlas ID 65 — Number of species potentially living in the cell

- **Nome nell’articolo/Atlas:** Species richness
- **Descrizione:** Biodiversity index based on cumulative species richness, including birds, fish/crustaceans, insects/clams, mammals, reptiles/amphibians, and other groups.
- **Tipo:** numeric
- **Ruolo ecologico:** `fragile_condition`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** number of species / index as defined by source
- **Codifica/trasformazione descritta nell’articolo:** As is.
- **Alias:** biodiversity, species richness, number of species, species count, potential species richness
- **Tag:** stressor_variable, fragile_condition, ecosystem_state, biodiversity, species_richness, ecological_indicator
- **Stato mappatura:** `strong_concept_match`
- **Nota da verificare:** The concept matches Atlas ID 65. The application's name does not make this a direct field observation, abundance estimate, or complete biodiversity census.

### Atlas ID 147 — Change in land use and cover in the past decade

- **Nome nell’articolo/Atlas:** Land use and cover anthropisation increase
- **Descrizione:** Changes in land use and vegetation cover, selecting classes with potential ecosystem impact: artificially shaped territories, utilised agricultural areas, and water bodies.
- **Tipo:** categorical
- **Ruolo ecologico:** `harmful_force`
- **Direzione nella metodologia dell’articolo:** `direct`
- **Unità:** classes
- **Codifica/trasformazione descritta nell’articolo:** Artificially shaped territories -> 1; utilised agricultural areas -> 0.5; water bodies -> -1; other classes -> 0.
- **Alias:** land use change, land-use change, anthropisation increase, land-use anthropisation, land cover change
- **Tag:** stressor_variable, harmful_force, anthropogenic_pressure, land_use, land_change, anthropisation
- **Stato mappatura:** `probable_alias_requires_encoding_check`
- **Nota da verificare:** Likely corresponds to Atlas ID 147, but the application's label is more general than the paper's anthropisation indicator. Verify the source CSV description and codes.

## API del file Python

- `get_variable_catalog()` — restituisce una copia del catalogo completo.
- `get_variable(nome)` — cerca usando nome canonico, nome leggibile, nome Atlas o alias.
- `get_variables_by_tag(tag)` — filtra per un tag esatto.
- `get_stressor_variables()` — restituisce le 12 variabili del gruppo metodologico dell’articolo.
- `get_harmful_forces()` — restituisce le 8 forze dannose.
- `get_fragile_conditions()` — restituisce i 4 indicatori di condizioni fragili.
- `get_provisional_mappings()` — restituisce le voci che richiedono un controllo tecnico.
- `format_variable_for_prompt(nome)` — genera una scheda testuale verificata da passare al contesto dell’LLM.

## Test eseguiti

Il modulo compila e supera i test smoke: 12 feature totali, 8 harmful forces, 4 fragile conditions, lookup per alias inclusi temperatura, biodiversità e grassland. I test verificano l’integrità tecnica del catalogo, non la corrispondenza definitiva dei codici CSV per tutte le feature.
