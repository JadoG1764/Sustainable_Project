# Requirements Specification — Sustainable Datacenter Siting Map

| | |
|---|---|
| **Course** | CS 4962 — Sustainable Computing (final project) |
| **Status** | Draft v0.1: research phase, no implementation yet |
| **Last updated** | 2026-10-18 |

Each requirement has a status:

- **Decided:** agreed and ready to implement.
- **Candidate:** the leading option, still to be confirmed.
- **TBD:** an open question; see [§9](#9-open-questions).

---

## 1. Purpose

Build a map of the United States that ranks locations by how suitable they are for a **new datacenter that minimizes environmental harm**. The map combines several environmental and practical factors into one composite suitability score. It shows where a datacenter would have:

- the lowest carbon, water and biodiversity impact;
- the shortest distance to existing transmission lines.

## 2. Scope
- Geographic extent: the **contiguous US (CONUS)**. Alaska and Hawaii are excluded. *(Decided 2026-10-18.)*
- Reference year: **2023** for every year-specific dataset. *(Decided 2026-10-18.)*
- Four scoring factors: biodiversity, carbon intensity, water scarcity, and existing infrastructure (distance to transmission lines). Natural hazard risk and climate/cooling demand were dropped on 2026-10-18.
- Hard exclusion of protected land.
- A composite suitability score and a map output.

## 3. Definitions

| Term | Meaning |
|---|---|
| **Zone** | An Electricity Maps grid zone. In the US these mostly correspond to balancing authorities (BAs). |
| **HUC8** | USGS 8-digit hydrologic unit (subbasin), roughly the size of a county. |
| **AWARE-US** | US-specific AWARE water scarcity characterization factors (Lee et al. 2018). |
| **OBI** | FABRIC Operational Biodiversity Index: biodiversity impact of electricity use from grid air pollution, in species·yr. |
| **GAP Status** | PAD-US code for management intent: 1–2 = managed for biodiversity, 3 = multiple use, 4 = no known mandate. |
| **MCDA** | Multi-criteria decision analysis. |

## 4. Functional Requirements

### 4.1 Spatial framework
| ID | Requirement | Status |
|---|---|---|
| FR-1.1 | The system shall resample every factor layer to **one common spatial unit** before scoring. | Decided |
| FR-1.2 | The common unit shall be the **H3 hexagon at resolution 6** (about 36 km²), with the resolution configurable. | Decided |
| FR-1.3 | Zone-level factors (carbon intensity, grid water stress, OBI) shall be assigned to each hexagon from the Electricity Maps zone containing the hexagon's **centroid**. | Decided |
| FR-1.4 | County-level factors (site AWARE-US) shall be assigned from the county containing the hexagon's centroid. | Decided |

### 4.2 Exclusions (hard constraints)
| ID | Requirement | Status |
|---|---|---|
| FR-2.1 | The system shall **exclude** all land in **PAD-US 4.1 with GAP Status 1 or 2**. | Decided |
| FR-2.2 | The system shall exclude **USFWS designated critical habitat**. | Decided |
| FR-2.3 | National Wetlands Inventory wetlands are not used in the first version. | Decided |
| FR-2.4 | PAD-US GAP Status 3 land is ignored (not penalized) in the first version. | Decided |

### 4.3 Carbon intensity
| ID | Requirement | Status |
|---|---|---|
| FR-3.1 | Carbon intensity shall come from the **Electricity Maps API** (academic access), in gCO₂eq/kWh per zone. | Decided |
| FR-3.2 | The system shall use a **consumption-based** carbon intensity, which includes imports, averaged over the 2023 reference year. | Candidate |
| FR-3.3 | Values may be cross-checked against the LBNL Water IMPACT per-BA CO₂e intensity. | Candidate |

### 4.4 Water scarcity
Water is scored by the **existing water-stress load** of the areas involved. There are two components:

| ID | Requirement | Status |
|---|---|---|
| FR-4.1 | Both water components shall use **AWARE-US** characterization factors. | Decided |
| FR-4.2 | **Site water stress:** AWARE-US at the site's **county**. | Decided |
| FR-4.3 | **Grid water stress:** AWARE-US at each **power plant's county**, **weighted by that plant's water consumption** (not its generation). | Decided |
| FR-4.4 | Plant water consumption shall come from **EIA thermoelectric cooling water data** (2023). Only thermoelectric plants are included; hydro and other non-thermoelectric plants are excluded from grid stress. | Decided |
| FR-4.5 | Grid water stress shall reflect **both local and imported electricity**. A zone's local plant-weighted stress shall be blended with the stress of the zones it imports from, using Electricity Maps import/export data. Each source is weighted by the **water embedded** in the electricity it supplies. | Decided |
| FR-4.6 | Exported electricity shall not count toward a zone's consumption-based grid stress. | Decided |
| FR-4.7 | AWARE-US factors shall be used at **annual** resolution. | Decided |
| FR-4.8 | Imports shall be traced **one hop** only (direct imports). | Decided |
| FR-4.9 | Hydropower reservoir evaporation is not counted, because hydro plants are excluded (FR-4.4). This assumption shall be documented. | Decided |
| FR-4.10 | The water factor shall be **50% site stress + 50% grid stress**, with the split configurable. | Decided |

### 4.5 Biodiversity
| ID | Requirement | Status |
|---|---|---|
| FR-5.1 | The biodiversity factor shall include the **FABRIC Operational Biodiversity Index (OBI)** per zone, in species·yr per kWh: grid SO₂/NOₓ/NH₃ emission factors × TRACI characterization factors (acidification, eutrophication, freshwater ecotoxicity) × ReCiPe 2016 Hierarchist endpoint factors (Shi et al. 2025). | Decided |
| FR-5.2 | The FABRIC Embodied Biodiversity Index (EBI) shall not be used, because it does not vary by site. | Decided |
| FR-5.3 | Per-zone emission rates shall be built from **plant-level** data aggregated to Electricity Maps zones by plant location: SO₂, NOₓ and generation from **eGRID2023**; NH₃ from the **2023 NEI** point-source data (fallback: eGRID2021 NH₃, documented). | Decided |
| FR-5.4 | Generation- or consumption-based emission rates. | TBD |
| FR-5.5 | The biodiversity factor shall include **NatureServe MoBI** as its habitat-importance input, to capture land-conversion harm. MoBI is one input, not the whole score. | Decided |
| FR-5.6 | The biodiversity factor shall be **50% OBI + 50% MoBI**, with the split configurable. | Decided |

### 4.6 Existing infrastructure
| ID | Requirement | Status |
|---|---|---|
| FR-6.1 | The infrastructure factor shall be **distance to the nearest existing transmission line**. No other infrastructure layers are used. | Decided |
| FR-6.2 | Transmission lines shall come from the EIA U.S. Energy Atlas (69–765 kV). | Candidate |
| FR-6.3 | Only lines at or above a **configurable minimum voltage** shall count, with a default of **200 kV**. | Decided |
| FR-6.4 | Distance to the nearest qualifying line shall be converted to a score, with closer being better. | Decided |
| FR-6.5 | The score shall use **linear decay**: 1 at the line, 0 at a **configurable cutoff** (default **50 km**). | Decided |
| FR-6.6 | Lines with unknown voltage and DC lines shall be excluded. | Decided |

### 4.7 Composite scoring
| ID | Requirement | Status |
|---|---|---|
| FR-7.1 | The system shall compute a **composite suitability score** from all four factors, following a GIS MCDA workflow: exclusions → normalization → weighting → aggregation. | Decided |
| FR-7.2 | Each factor shall be normalized to a common scale with a consistent direction (for example 0–1, higher = better). | Decided |
| FR-7.3 | The first version shall use a **weighted linear combination with equal weights** (0.25 per factor), with weights configurable. AHP, TOPSIS or data-driven weights may follow. | Decided (first version) |
| FR-7.4 | The system shall include a **sensitivity analysis** showing how rankings change as weights vary. | Candidate |
| FR-7.5 | The score shall be computed for every non-excluded unit, or by shortlisting low-carbon zones and then ranking within them. | TBD |

### 4.8 Output
| ID | Requirement | Status |
|---|---|---|
| FR-8.1 | The system shall produce a **map** of composite suitability over the study area, with excluded land clearly marked. | Decided |
| FR-8.2 | The map shall let the user view each individual factor layer as well as the composite. | Candidate |
| FR-8.3 | The system shall output a ranked list of the top candidate locations with their per-factor scores. | Candidate |
| FR-8.4 | The map shall be an **interactive web map** (for example folium or kepler.gl). | Decided |

## 5. Data Requirements

| Factor | Dataset | Provider | Status |
|---|---|---|---|
| Exclusion | PAD-US 4.1 (GAP Status 1–2) | USGS GAP | Decided |
| Exclusion | Critical Habitat | USFWS ECOS | Decided |
| Carbon | Carbon intensity, power breakdown, imports/exports (2023) | Electricity Maps (academic API, cleared) | Decided |
| Carbon / water / biodiversity | Zone boundaries | Electricity Maps `zone-finder` | Candidate |
| Water | AWARE-US county characterization factors (monthly, averaged to annual) | Argonne GREET, greet.es.anl.gov/aware (Lee et al. 2018) | Decided (manual download; check terms) |
| Water / site | County boundaries | US Census TIGER/Line | Decided (implied) |
| Water | Thermoelectric cooling water data (2023) | EIA | Decided |
| Water (validation) | Water IMPACT per-BA water intensity | LBNL | Candidate |
| Biodiversity | OBI method and characterization factors | FABRIC (Shi et al. 2025; MIT license) | Decided |
| Biodiversity | Plant SO₂, NOₓ and generation (2023) | EPA eGRID2023 | Decided |
| Biodiversity | Plant NH₃ (2023) | EPA 2023 NEI point sources: facility summary or SMOKE FF10 point file (fallback: eGRID2021 NH₃) | Decided (NH₃ confirmed present) |
| Biodiversity | Map of Biodiversity Importance | NatureServe (CC BY-NC) | Decided |
| Spatial | H3 hexagon grid | Uber H3 | Decided |
| Infrastructure | Transmission lines | EIA Energy Atlas (ex-HIFLD) | Candidate |

**Note:** HIFLD Open was shut down on 2025-08-26. Links to it are dead, so use the EIA Energy Atlas or the archived copies.

## 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | **Reproducibility:** raw data shall not be committed. The repository shall contain scripts that download and rebuild every dataset. |
| NFR-2 | **Provenance:** every dataset's source, version, date retrieved and license shall be recorded. |
| NFR-3 | **Secrets:** the Electricity Maps API key shall be read from an environment variable and never committed. |
| NFR-4 | **Licensing:** all data shall be used within its license terms (for example MoBI is CC BY-NC, and Electricity Maps academic terms require attribution). |
| NFR-5 | **Transparency:** all assumptions (hydro evaporation, normalization, weights, reference year) shall be documented next to the results. |
| NFR-6 | **Performance:** processing shall be feasible on a personal machine at CONUS scale. Large layers (NWI, 30 m rasters) shall be aggregated to the analysis unit early. |
| NFR-7 | **Language / tooling:** Python. Specific libraries are TBD. |

## 7. Assumptions & Constraints

- The study area is effectively CONUS, because of the extent of the source data.
- Carbon intensity and grid water stress are **uniform within a zone**, so they differentiate sites between zones but not within them.
- Electricity Maps does not report cooling type. Fleet-average water factors per fuel therefore come from EIA plant-level data rather than from Macknick 2012 averages, which are outdated for today's fleet.
- EIA water reporting is required only for plants of at least 100 MW, and it has known gaps. Missing values are filled with literature factors.
- Grid water stress counts thermoelectric plants only. Hydro reservoir evaporation and other non-thermoelectric water use are not counted, so stress is understated in hydro-heavy zones.
- The FABRIC OBI captures grid air-pollution harm only, at zone level, and uses one global characterization factor regardless of local ecosystem sensitivity. Land-conversion harm is covered by the habitat input and the exclusions.

## 8. Validation & Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-1 | No excluded land (PAD-US GAP 1–2, critical habitat) receives a suitability score. |
| AC-2 | Every factor layer covers the full study area, or its gaps are explicitly flagged. |
| AC-3 | Per-zone plant water intensities are checked against LBNL Water IMPACT and the literature (US average ≈ 3.14 L/kWh). |
| AC-4 | Results are broadly consistent with published siting findings, or any differences are explained. Example: Xiao et al. (2025) found the Midwest and windbelt (TX, MT, NE, SD) had the best combined carbon-and-water profile. |
| AC-5 | A sensitivity analysis shows how the top-ranked locations change under different weightings. |
| AC-6 | The map and write-up document every data source, assumption and limitation. |

## 9. Open Questions

1. AWARE-US spreadsheet: terms of use, and whether a newer version than 2020 exists.
2. 2023 NEI file layout: column names, the power-plant sector filter, and whether ORIS plant IDs are present for joining to eGRID.
3. Generation- or consumption-based emission rates for the OBI; verify FABRIC's Γ/Φ values.
4. How Electricity Maps' consumption breakdown handles exports.
5. Formal MCDA method and sensitivity analysis (deferred; equal-weight WLC first).
6. Tech stack and project structure.

## 10. Key References

- Siddik, Shehabi & Marston (2021). The environmental footprint of data centers in the United States. *Environmental Research Letters*. doi:10.1088/1748-9326/abfba1
- Siddik, Shehabi, Rao & Marston (2024). Spatially and temporally detailed water and carbon footprints of U.S. electricity generation and use. *Water Resources Research*. doi:10.1029/2024WR038350
- Lee et al. (2018). AWARE-US: Quantifying water stress impacts of energy systems in the United States. *Science of the Total Environment*.
- Macknick et al. (2012). Operational water consumption and withdrawal factors for electricity generating technologies. *Environmental Research Letters* 7:045802.
- Jin, Behrens, Tukker & Scherer (2019). Water use of electricity technologies: A global meta-analysis. *Renewable and Sustainable Energy Reviews* 115.
- Grubert & Sanders (2018). Water use in the United States energy system. *Environmental Science & Technology*. doi:10.1021/acs.est.8b00139
- Xiao et al. (2025). Environmental impact and net-zero pathways for sustainable AI servers in the USA. *Nature Sustainability*.
- Shi, Kumar, Hua & Ding (2025). When Servers Meet Species: A Fab-to-Grave Lens on Computing's Biodiversity Impact. HotCarbon '25. arXiv:2506.20442. Code: github.com/TianyaoShi/FABRIC
- Talukder et al. (2026). Balancing Bits and Drops: Stress-Adjusted Water Management for Data Centers. arXiv:2607.22617.
