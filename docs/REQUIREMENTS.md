# Requirements Specification — Sustainable Datacenter Siting Map

| | |
|---|---|
| **Course** | CS 4962 — Sustainable Computing (final project) |
| **Status** | Draft v0.1: research phase, no implementation yet |
| **Last updated** | 2026-09-29 |

Each requirement has a status:

- **Decided:** agreed and ready to implement.
- **Candidate:** the leading option, still to be confirmed.
- **TBD:** an open question; see [§9](#9-open-questions).

---

## 1. Purpose

Build a map of the United States that ranks locations by how suitable they are for a **new datacenter that minimizes environmental harm**. The map combines several environmental and practical factors into one composite suitability score. It shows where a datacenter would have:

- the lowest carbon, water and biodiversity impact;
- the lowest exposure to natural hazards;
- the best use of existing infrastructure.

## 2. Scope
- Geographic extent: **United States**. In practice this is the **contiguous US (CONUS)**, because several core datasets (NADP TDep, NCLD, MoBI, Annual NLCD) cover CONUS only. *(Candidate: confirm whether Alaska and Hawaii are dropped.)*
- Six scoring factors: biodiversity, carbon intensity, water scarcity, existing infrastructure, natural hazard risk, and climate/cooling demand.
- Hard exclusion of protected land.
- A composite suitability score and a map output.

## 3. Definitions

| Term | Meaning |
|---|---|
| **Zone** | An Electricity Maps grid zone. In the US these mostly correspond to balancing authorities (BAs). |
| **HUC8** | USGS 8-digit hydrologic unit (subbasin), roughly the size of a county. |
| **AWARE-US** | US-specific AWARE water scarcity characterization factors (Lee et al. 2018). |
| **Critical load** | The deposition level below which harmful ecological effects are not expected (kg N/ha/yr). |
| **Exceedance** | Current N deposition minus the critical load. A positive value means the ecosystem is already over its threshold. |
| **GAP Status** | PAD-US code for management intent: 1–2 = managed for biodiversity, 3 = multiple use, 4 = no known mandate. |
| **MCDA** | Multi-criteria decision analysis. |

## 4. Functional Requirements

### 4.1 Spatial framework
| ID | Requirement | Status |
|---|---|---|
| FR-1.1 | The system shall resample every factor layer to **one common spatial unit** before scoring. | Decided |
| FR-1.2 | The common unit shall be a grid cell (for example H3 or a regular raster), a county, or a zone. | TBD |
| FR-1.3 | Zone-level factors (carbon intensity, grid water stress) shall be joined to finer units using Electricity Maps zone boundaries. | Decided |

### 4.2 Exclusions (hard constraints)
| ID | Requirement | Status |
|---|---|---|
| FR-2.1 | The system shall **exclude** all land in **PAD-US 4.1 with GAP Status 1 or 2**. | Decided |
| FR-2.2 | The system should exclude **USFWS designated critical habitat**. | Candidate |
| FR-2.3 | The system should exclude **National Wetlands Inventory** wetlands, or penalize by percent wetland per unit. | Candidate |
| FR-2.4 | PAD-US GAP Status 3 land shall be penalized or ignored. | TBD |

### 4.3 Carbon intensity
| ID | Requirement | Status |
|---|---|---|
| FR-3.1 | Carbon intensity shall come from the **Electricity Maps API** (academic access), in gCO₂eq/kWh per zone. | Decided |
| FR-3.2 | The system shall use a **consumption-based** carbon intensity, which includes imports, averaged over one chosen reference year. | Candidate |
| FR-3.3 | Values may be cross-checked against the LBNL Water IMPACT per-BA CO₂e intensity. | Candidate |

### 4.4 Water scarcity
Water is scored by the **existing water-stress load** of the areas involved. There are two components:

| ID | Requirement | Status |
|---|---|---|
| FR-4.1 | Both water components shall use **AWARE-US** characterization factors. | Decided |
| FR-4.2 | **Site water stress:** AWARE-US at the site's HUC8 (or county). | Decided |
| FR-4.3 | **Grid water stress:** AWARE-US at each **power plant's** HUC8, **weighted by that plant's water consumption** (not its generation). | Decided |
| FR-4.4 | Plant water consumption shall come from **EIA thermoelectric cooling water data** (the most recent year) for thermoelectric plants. For hydro and other non-thermoelectric plants it shall come from literature factors (Macknick 2012, Jin 2019, Grubert & Sanders 2018). | Decided |
| FR-4.5 | Grid water stress shall reflect **both local and imported electricity**. A zone's local plant-weighted stress shall be blended with the stress of the zones it imports from, using Electricity Maps import/export data. Each source is weighted by the **water embedded** in the electricity it supplies. | Decided |
| FR-4.6 | Exported electricity shall not count toward a zone's consumption-based grid stress. | Decided |
| FR-4.7 | AWARE-US factors shall be used at annual or monthly resolution. | TBD |
| FR-4.8 | Imports shall be traced one hop only, or across several hops. | TBD |
| FR-4.9 | The treatment of hydropower reservoir evaporation shall be chosen and documented. | TBD |
| FR-4.10 | How site and grid stress combine into the water factor is deferred with the composite formula. | TBD |

### 4.5 Biodiversity
| ID | Requirement | Status |
|---|---|---|
| FR-5.1 | The biodiversity factor shall include **nitrogen-deposition exceedance** = NADP **TDep** total N deposition (latest year) − **Simkin** critical load (NCLD), in kg N/ha/yr. | Candidate |
| FR-5.2 | Open- or closed-canopy Simkin critical loads shall be chosen from land cover (Annual NLCD), or the lower of the two used to be conservative. | Candidate |
| FR-5.3 | The factor may add lichen (Geiser et al.) and tree (Dalton et al. 2024) receptors, taking the worst-case exceedance per unit. | TBD |
| FR-5.4 | The biodiversity factor shall include a **habitat-importance input** to capture land-conversion harm, either NatureServe **MoBI** or USGS GAP species richness. | Candidate (MoBI leading) |
| FR-5.5 | MoBI, if used, shall be **one input** to the composite score, not the whole score. | Decided |
| FR-5.6 | How exceedance combines with the habitat input into a biodiversity sub-score. | TBD |

### 4.6 Existing infrastructure
| ID | Requirement | Status |
|---|---|---|
| FR-6.1 | The infrastructure factor shall reward proximity to existing **transmission** (EIA Energy Atlas lines, 69–765 kV) and **substations** (OpenStreetMap). | Candidate |
| FR-6.2 | It shall reward **fiber / network availability**: FCC National Broadband Map fiber availability, and/or PeeringDB facilities and IXPs. | Candidate |
| FR-6.3 | It shall reward **previously developed land** (Annual NLCD developed classes) and **brownfields** (EPA RE-Powering). | Candidate |
| FR-6.4 | It may include grid headroom (LBNL Queued Up) and existing-datacenter proximity (PNNL IM3 Data Center Atlas). | TBD |
| FR-6.5 | How each layer becomes a score (for example distance to the nearest line of at least X kV, or fiber presence per cell). | TBD |

### 4.7 Natural hazard risk
| ID | Requirement | Status |
|---|---|---|
| FR-7.1 | The hazard factor shall come from the **FEMA National Risk Index** (census tract or county). | Decided |
| FR-7.2 | The factor shall use the overall NRI risk score, or a subset of hazards relevant to datacenters (for example flooding, wildfire, hurricane, tornado, earthquake, heat wave). | TBD |

### 4.8 Climate / cooling demand
| ID | Requirement | Status |
|---|---|---|
| FR-8.1 | The climate factor shall reward cooler, drier climates with more free-cooling potential. | Decided |
| FR-8.2 | The metric shall be annual hours below a wet-bulb threshold, cooling degree days, or another measure. The source shall be NOAA nClimGrid, ERA5-Land or the Green Grid free-cooling data. | TBD |

### 4.9 Composite scoring
| ID | Requirement | Status |
|---|---|---|
| FR-9.1 | The system shall compute a **composite suitability score** from all six factors, following a GIS MCDA workflow: exclusions → normalization → weighting → aggregation. | Decided |
| FR-9.2 | Each factor shall be normalized to a common scale with a consistent direction (for example 0–1, higher = better). | Decided |
| FR-9.3 | The weighting method shall be weighted linear combination, AHP, TOPSIS or data-driven weights. | TBD (deferred) |
| FR-9.4 | The system shall include a **sensitivity analysis** showing how rankings change as weights vary. | Candidate |
| FR-9.5 | The score shall be computed for every non-excluded unit, or by shortlisting low-carbon zones and then ranking within them. | TBD |

### 4.10 Output
| ID | Requirement | Status |
|---|---|---|
| FR-10.1 | The system shall produce a **map** of composite suitability over the study area, with excluded land clearly marked. | Decided |
| FR-10.2 | The map shall let the user view each individual factor layer as well as the composite. | Candidate |
| FR-10.3 | The system shall output a ranked list of the top candidate locations with their per-factor scores. | Candidate |
| FR-10.4 | The map shall be interactive (web) or static. | TBD |

## 5. Data Requirements

| Factor | Dataset | Provider | Status |
|---|---|---|---|
| Exclusion | PAD-US 4.1 (GAP Status 1–2) | USGS GAP | Decided |
| Exclusion | Critical Habitat | USFWS ECOS | Candidate |
| Exclusion | National Wetlands Inventory | USFWS | Candidate |
| Carbon | Carbon intensity, power breakdown, imports/exports | Electricity Maps (academic API) | Decided |
| Carbon / water | Zone boundaries | Electricity Maps `zone-finder` | Candidate |
| Water | AWARE-US characterization factors | Lee et al. 2018 | Decided (**table still to be located**) |
| Water | Thermoelectric cooling water data (2014–2024) | EIA | Decided |
| Water | Non-thermoelectric water factors | Macknick 2012; Jin 2019; Grubert & Sanders 2018 | Decided |
| Water | HUC8 watershed boundaries | USGS WBD | Decided (implied) |
| Water (validation) | Water IMPACT per-BA water intensity | LBNL | Candidate |
| Biodiversity | TDep total N deposition | NADP | Candidate |
| Biodiversity | Simkin critical loads (`NCLD_EMP_ER34_Rasters_Simkin_v321.zip`) | NCLD / EPA | Candidate |
| Biodiversity | Map of Biodiversity Importance | NatureServe (CC BY-NC) | Candidate |
| Biodiversity / infra | Annual NLCD land cover | USGS / MRLC | Candidate |
| Infrastructure | Transmission lines | EIA Energy Atlas (ex-HIFLD) | Candidate |
| Infrastructure | Substations | OpenStreetMap | Candidate |
| Infrastructure | Broadband / fiber availability | FCC BDC | Candidate |
| Infrastructure | Interconnection facilities / IXPs | PeeringDB | Candidate |
| Infrastructure | Brownfields | EPA RE-Powering | Candidate |
| Infrastructure | Existing datacenters (reference) | PNNL IM3 Atlas | Candidate |
| Hazard | National Risk Index | FEMA | Decided |
| Climate | Gridded temperature / wet-bulb | NOAA nClimGrid or ERA5-Land | TBD |

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
- Critical loads capture harm from air pollution only. Land-conversion harm is covered by the habitat input and the exclusions.

## 8. Validation & Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-1 | No excluded land (PAD-US GAP 1–2) receives a suitability score. |
| AC-2 | Every factor layer covers the full study area, or its gaps are explicitly flagged. |
| AC-3 | Per-zone plant water intensities are checked against LBNL Water IMPACT and the literature (US average ≈ 3.14 L/kWh). |
| AC-4 | Results are broadly consistent with published siting findings, or any differences are explained. Example: Xiao et al. (2025) found the Midwest and windbelt (TX, MT, NE, SD) had the best combined carbon-and-water profile. |
| AC-5 | A sensitivity analysis shows how the top-ranked locations change under different weightings. |
| AC-6 | The map and write-up document every data source, assumption and limitation. |

## 9. Open Questions

1. Spatial unit of analysis (grid cell, county or zone).
2. Whether the scope is CONUS only or all 50 states.
3. Where to download the AWARE-US factor table and its license; annual or monthly factors.
4. One-hop or multi-hop import tracing; how to handle hydropower evaporation.
5. How to combine site and grid water stress.
6. Excluding critical habitat and wetlands; how to treat GAP Status 3.
7. MoBI vs GAP richness; adding lichen and tree receptors; how to build the biodiversity sub-score.
8. Which infrastructure layers to use and how to score them.
9. FEMA NRI overall score or a subset of hazards.
10. The climate metric and its dataset.
11. Composite method, normalization and weights (deferred).
12. Interactive or static map; tech stack.

## 10. Key References

- Siddik, Shehabi & Marston (2021). The environmental footprint of data centers in the United States. *Environmental Research Letters*. doi:10.1088/1748-9326/abfba1
- Siddik, Shehabi, Rao & Marston (2024). Spatially and temporally detailed water and carbon footprints of U.S. electricity generation and use. *Water Resources Research*. doi:10.1029/2024WR038350
- Lee et al. (2018). AWARE-US: Quantifying water stress impacts of energy systems in the United States. *Science of the Total Environment*.
- Macknick et al. (2012). Operational water consumption and withdrawal factors for electricity generating technologies. *Environmental Research Letters* 7:045802.
- Jin, Behrens, Tukker & Scherer (2019). Water use of electricity technologies: A global meta-analysis. *Renewable and Sustainable Energy Reviews* 115.
- Grubert & Sanders (2018). Water use in the United States energy system. *Environmental Science & Technology*. doi:10.1021/acs.est.8b00139
- Xiao et al. (2025). Environmental impact and net-zero pathways for sustainable AI servers in the USA. *Nature Sustainability*.
- Clark et al. (2018): national critical load exceedance; Simkin et al.: herbaceous species richness critical loads (NCLD).
- Talukder et al. (2026). Balancing Bits and Drops: Stress-Adjusted Water Management for Data Centers. arXiv:2607.22617.
