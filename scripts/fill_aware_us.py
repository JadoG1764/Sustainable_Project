"""Fill AWARE-US county gaps with the average of neighboring counties.

Joins AWARE-US county factors to Census 2020 counties (CONUS), whose codes match
AWARE-US (old Connecticut counties). Counties with no AWARE-US row or a -1 value
get the mean of their touching neighbors; this repeats until every county has a
value, so counties surrounded by gaps fill from the next ring out. Islands with
no touching neighbors use the 3 nearest counties that have values.

Usage: python scripts/fill_aware_us.py [data_dir]   (default: ./data)
Output: <data_dir>/processed/aware_us_county_filled.csv
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

NON_CONUS_STATEFP = {"02", "15", "60", "66", "69", "72", "78"}
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
CF_COLUMNS = ["annual_cf"] + [f"{m}_cf" for m in MONTHS]


def load_aware(path):
    df = pd.read_excel(path, sheet_name="Data", header=None, skiprows=2, dtype={0: str})
    df = df.iloc[:, :16]
    df.columns = ["fips", "state", "county"] + CF_COLUMNS
    df = df.dropna(subset=["fips"])
    df["fips"] = df["fips"].str.zfill(5)
    df[CF_COLUMNS] = df[CF_COLUMNS].astype(float).mask(lambda x: x < 0)  # -1 = no data
    return df


def load_counties(path):
    counties = gpd.read_file(f"zip://{path}")
    counties = counties[~counties["STATEFP"].isin(NON_CONUS_STATEFP)]
    return counties[["GEOID", "NAME", "STUSPS", "geometry"]].rename(columns={"GEOID": "fips"}).to_crs(5070)


def fill_from_neighbors(gdf):
    neighbors = gpd.sjoin(gdf[["fips", "geometry"]], gdf[["fips", "geometry"]], predicate="touches")
    neighbors = neighbors[neighbors["fips_left"] != neighbors["fips_right"]]
    adjacency = neighbors.groupby("fips_left")["fips_right"].apply(list).to_dict()

    values = gdf.set_index("fips")[CF_COLUMNS]
    method = pd.Series("aware_us", index=values.index).where(values["annual_cf"].notna(), None)

    while values["annual_cf"].isna().any():
        missing = values.index[values["annual_cf"].isna()]
        filled_any = False
        for fips in missing:
            known = [n for n in adjacency.get(fips, []) if pd.notna(values.at[n, "annual_cf"])]
            if known:
                values.loc[fips] = values.loc[known].mean()
                method[fips] = "neighbor_mean"
                filled_any = True
        if not filled_any:
            break

    # Islands (no touching neighbors): use the 3 nearest counties with values.
    centroids = gdf.set_index("fips").geometry.centroid
    for fips in values.index[values["annual_cf"].isna()]:
        known = values.index[values["annual_cf"].notna()]
        nearest = centroids[known].distance(centroids[fips]).nsmallest(3).index
        values.loc[fips] = values.loc[nearest].mean()
        method[fips] = "nearest_3_mean"

    return values.assign(fill_method=method)


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    aware = load_aware(data_dir / "raw/aware_us/AWARE_US_CF.xlsx")
    counties = load_counties(data_dir / "raw/counties/cb_2020_us_county_500k.zip")

    gdf = counties.merge(aware.drop(columns=["state", "county"]), on="fips", how="left")
    filled = fill_from_neighbors(gdf)

    out = counties.drop(columns="geometry").set_index("fips").join(filled).reset_index()
    out_path = data_dir / "processed/aware_us_county_filled.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print(f"{len(out)} CONUS counties -> {out_path}")
    print(out["fill_method"].value_counts().to_string())
    print(out.loc[out["fill_method"] != "aware_us", ["fips", "NAME", "STUSPS", "annual_cf", "fill_method"]].to_string(index=False))


if __name__ == "__main__":
    main()
