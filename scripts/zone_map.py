"""Build the CONUS H3 grid, assign each hexagon an Electricity Maps zone, and map it.

Each H3 cell takes the zone that contains its centroid; cells whose centroid falls
outside every zone polygon (coastline mismatches) take the nearest zone.

Usage: python scripts/zone_map.py [data_dir] [h3_resolution]   (defaults: ./data, 6)
Outputs: <data_dir>/processed/h3_res<r>_zones.parquet
         <data_dir>/processed/zone_map_res<r>.png
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import h3
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from shapely.geometry import Point, Polygon, box

NON_CONUS_STATEFP = {"02", "15", "60", "66", "69", "72", "78"}
ALBERS = 5070

# Light tints of the reference categorical hues. Zone identity is carried by the
# label and the boundary line; fill color only separates neighbors.
ZONE_FILLS = ["#b7d3f6", "#f7c3ad", "#a8e0c8", "#f5c8d9", "#cbc4f1", "#f8dc99"]
# Sequential blue ramp (steps 100-700) for carbon intensity.
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INK, INK_MUTED, BOUNDARY, SURFACE = "#0b0b0b", "#52514e", "#3d3d3a", "#fcfcfb"


def load_conus(data_dir):
    counties = gpd.read_file(f"zip://{data_dir / 'raw/counties/cb_2020_us_county_500k.zip'}")
    counties = counties[~counties["STATEFP"].isin(NON_CONUS_STATEFP)]
    states = counties.dissolve(by="STATEFP")
    return states.to_crs(4326).union_all(), states.to_crs(ALBERS)


def load_zones(data_dir):
    geo = json.loads((data_dir / "raw/zones/geo.generated.json").read_text())["zoneToGeometryFeatures"]
    feats = [f for zone, fs in geo.items() if zone.startswith("US-") and not zone.startswith(("US-AK", "US-HI")) for f in fs]
    zones = gpd.GeoDataFrame.from_features(feats, crs=4326).dissolve(by="zoneName").reset_index()
    return zones.rename(columns={"zoneName": "zone"})[["zone", "geometry"]]


def build_cells(conus, resolution):
    cells = set()
    for poly in getattr(conus, "geoms", [conus]):
        cells |= set(h3.geo_to_cells(poly.__geo_interface__, resolution))
    cells = sorted(cells)
    centroids = [Point(lng, lat) for lat, lng in (h3.cell_to_latlng(c) for c in cells)]
    return gpd.GeoDataFrame({"h3": cells}, geometry=centroids, crs=4326)


def assign_zones(cells, zones):
    joined = gpd.sjoin(cells, zones, predicate="within", how="left").drop(columns="index_right")
    joined = joined[~joined.index.duplicated()]
    missing = joined["zone"].isna()
    if missing.any():
        near = gpd.sjoin_nearest(joined.loc[missing, ["h3", "geometry"]].to_crs(ALBERS), zones.to_crs(ALBERS), how="left")
        near = near[~near.index.duplicated()]
        joined.loc[missing, "zone"] = near["zone"]
    joined["assigned_by"] = "centroid_in_zone"
    joined.loc[missing, "assigned_by"] = "nearest_zone"
    return joined


def neighbor_colors(zones):
    """Greedy graph coloring so touching zones get different fills."""
    z = zones.to_crs(ALBERS)
    pairs = gpd.sjoin(z, z.assign(geometry=z.buffer(2000)), predicate="intersects")
    graph = nx.Graph()
    graph.add_nodes_from(z["zone"])
    graph.add_edges_from((a, b) for a, b in zip(pairs["zone_left"], pairs["zone_right"]) if a != b)
    coloring = nx.greedy_color(graph, strategy="largest_first")
    return {zone: ZONE_FILLS[i % len(ZONE_FILLS)] for zone, i in coloring.items()}


def hex_polygons(cells):
    polys = [Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in cells["h3"]]
    return cells.drop(columns="geometry").set_geometry(gpd.GeoSeries(polys, crs=4326)).to_crs(ALBERS)


def plot(hexes, zones, states, carbon, resolution, out_path):
    zones_a = zones.to_crs(ALBERS)
    fills = neighbor_colors(zones)
    hexes = hexes.merge(carbon, on="zone", how="left")

    fig = plt.figure(figsize=(16, 14), facecolor=SURFACE)
    ax_zone = fig.add_axes([0.02, 0.50, 0.62, 0.45])
    ax_zoom = fig.add_axes([0.66, 0.53, 0.32, 0.40])
    ax_ci = fig.add_axes([0.02, 0.03, 0.62, 0.45])
    ax_note = fig.add_axes([0.66, 0.05, 0.32, 0.40])
    for ax in (ax_zone, ax_zoom, ax_ci, ax_note):
        ax.set_axis_off()
        ax.set_facecolor(SURFACE)

    # Panel 1: zones, labelled.
    hexes.plot(ax=ax_zone, color=hexes["zone"].map(fills), linewidth=0)
    zones_a.boundary.plot(ax=ax_zone, color=BOUNDARY, linewidth=0.6)
    states.boundary.plot(ax=ax_zone, color="#ffffff", linewidth=0.3, alpha=0.7)
    for _, row in zones_a.iterrows():
        if row.geometry.area > 2.5e10:  # label zones larger than ~25,000 km²
            p = row.geometry.representative_point()
            ax_zone.annotate(row["zone"].removeprefix("US-"), (p.x, p.y), ha="center", va="center", fontsize=6.5, color=INK)
    ax_zone.set_title(f"{zones['zone'].nunique()} Electricity Maps zones on the CONUS H3 grid (resolution {resolution})",
                      loc="left", fontsize=13, color=INK, fontweight="bold")

    # Panel 2: zoom showing individual hexagons.
    center = zones_a.loc[zones_a["zone"] == "US-CAR-DUK", "geometry"].iloc[0].centroid
    window = box(center.x - 220_000, center.y - 180_000, center.x + 220_000, center.y + 180_000)
    zoom = hexes[hexes.intersects(window)]
    zoom.plot(ax=ax_zoom, color=zoom["zone"].map(fills), edgecolor="#ffffff", linewidth=0.25)
    zones_a.clip(window).boundary.plot(ax=ax_zoom, color=BOUNDARY, linewidth=1.2)
    states.clip(window).boundary.plot(ax=ax_zoom, color=INK_MUTED, linewidth=0.4, linestyle=":")
    for _, row in zones_a.clip(window).iterrows():
        if row.geometry.area > 4e9:
            p = row.geometry.representative_point()
            ax_zoom.annotate(row["zone"].removeprefix("US-"), (p.x, p.y), ha="center", fontsize=8, color=INK,
                             bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.85))
    ax_zoom.set_xlim(window.bounds[0], window.bounds[2])
    ax_zoom.set_ylim(window.bounds[1], window.bounds[3])
    ax_zoom.set_title("Zoom: the Carolinas, one zone per hexagon (~36 km² each)", loc="left", fontsize=10, color=INK)
    ax_zone.add_patch(plt.Rectangle(window.bounds[:2], window.bounds[2] - window.bounds[0], window.bounds[3] - window.bounds[1],
                                    fill=False, edgecolor=INK, linewidth=1))

    # Panel 3: 2023 carbon intensity per hexagon (inherited from its zone).
    bounds = [0, 100, 200, 300, 400, 500, 650, 900]
    cmap, norm = ListedColormap(SEQ_BLUE), BoundaryNorm(bounds, len(SEQ_BLUE))
    hexes.plot(ax=ax_ci, column="carbon_intensity", cmap=cmap, norm=norm, linewidth=0)
    zones_a.boundary.plot(ax=ax_ci, color="#ffffff", linewidth=0.5)
    states.boundary.plot(ax=ax_ci, color=INK_MUTED, linewidth=0.25, alpha=0.6)
    cax = fig.add_axes([0.06, 0.06, 0.25, 0.012])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal", ticks=bounds)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, colors=INK_MUTED, length=0)
    cb.set_label("gCO₂eq/kWh (lifecycle, consumption-based)", fontsize=8, color=INK_MUTED)
    ax_ci.set_title("Every hexagon inherits its zone's 2023 carbon intensity", loc="left", fontsize=13, color=INK, fontweight="bold")

    # Panel 4: summary text.
    by = hexes["assigned_by"].value_counts()
    top = carbon[carbon["zone"].isin(zones["zone"])].sort_values("carbon_intensity")
    lines = [
        "Grid summary",
        f"H3 resolution {resolution}: {len(hexes):,} hexagons",
        f"Zones with a service area: {zones['zone'].nunique()}",
        f"Assigned by centroid: {by.get('centroid_in_zone', 0):,}",
        f"Assigned to nearest zone (coast): {by.get('nearest_zone', 0):,}",
        "",
        "Lowest carbon intensity (gCO₂eq/kWh)",
        *[f"  {z.removeprefix('US-'):<12} {v:>4.0f}" for z, v in top.head(4).itertuples(index=False)],
        "Highest",
        *[f"  {z.removeprefix('US-'):<12} {v:>4.0f}" for z, v in top.tail(4).itertuples(index=False)],
        "",
        "Not on the map: US-CAR-YAD, US-NW-GRID, US-SE-SEPA",
        "(generation-only, no service area; import sources only)",
    ]
    ax_note.text(0, 1, "\n".join(lines), va="top", ha="left", fontsize=10, color=INK, family="monospace")

    fig.savefig(out_path, dpi=150, facecolor=SURFACE)


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    resolution = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    out_dir = data_dir / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    conus, states = load_conus(data_dir)
    zones = load_zones(data_dir)
    cells = assign_zones(build_cells(conus, resolution), zones)
    cells[["h3", "zone", "assigned_by"]].to_parquet(out_dir / f"h3_res{resolution}_zones.parquet", index=False)

    ci = json.loads((data_dir / "raw/electricitymaps/carbon_intensity_2023_yearly.json").read_text())
    carbon = pd.DataFrame([(z, d["data"][0]["carbonIntensity"]) for z, d in ci.items() if d.get("data")],
                          columns=["zone", "carbon_intensity"])

    plot(hex_polygons(cells), zones, states, carbon, resolution, out_dir / f"zone_map_res{resolution}.png")
    print(f"{len(cells):,} cells, {cells['zone'].nunique()} zones")
    print(cells["assigned_by"].value_counts().to_string())


if __name__ == "__main__":
    main()
