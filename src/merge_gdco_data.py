"""
One-time migration: merge the two source CSVs into a single ``gdco_data.csv``.

``gdco_data.csv`` keeps ``gdco_reference.csv`` as the leading table (one row per
appid, all original columns preserved) and adds two aligned, JSON-encoded array
columns holding the per-game tags from ``gdco_tags.csv``:

    tags        e.g. ["Simulation", "Strategy", "Indie"]
    tagCounts   e.g. [240, 180, 95]      # gdco_tags."nb", aligned so tagCounts[i]
                                         # is the player count for tags[i]

Tags whose appid is absent from the reference table are dropped (the reference is
leading); reference games with no tags get empty arrays. Run from the repo root:

    python ./src/merge_gdco_data.py
"""
import json

import pandas as pd

REFERENCE_CSV = "data/gdco_reference.csv"
TAGS_CSV = "data/gdco_tags.csv"
OUTPUT_CSV = "data/gdco_data.csv"


def merge(reference_csv=REFERENCE_CSV, tags_csv=TAGS_CSV, output_csv=OUTPUT_CSV):
    reference = pd.read_csv(reference_csv)
    tags = pd.read_csv(tags_csv)

    # Diagnostics — confirm the assumptions behind the round-trip.
    print(f"reference: {reference.shape[0]} rows, {reference.shape[1]} cols, "
          f"appid unique: {reference['appid'].is_unique}")
    print(f"tags: {tags.shape[0]} rows, nb dtype: {tags['nb'].dtype}, "
          f"nb has NaN: {bool(tags['nb'].isna().any())}")

    # Group the (nb, tag) rows per appid, preserving their order in gdco_tags.csv.
    grouped = tags.groupby("appid", sort=False)
    tag_lists = grouped["tag"].apply(list)
    nb_lists = grouped["nb"].apply(lambda s: [int(x) for x in s])

    # Attach as aligned arrays; appids without tags get empty lists.
    ref_tags = reference["appid"].map(tag_lists)
    ref_nb = reference["appid"].map(nb_lists)
    n_with_tags = int(ref_tags.notna().sum())

    reference["tags"] = [t if isinstance(t, list) else [] for t in ref_tags]
    reference["tagCounts"] = [n if isinstance(n, list) else [] for n in ref_nb]

    # JSON-encode the array columns so they survive the CSV round-trip intact.
    reference["tags"] = reference["tags"].apply(json.dumps)
    reference["tagCounts"] = reference["tagCounts"].apply(json.dumps)

    reference.to_csv(output_csv, index=False)
    print(f"Wrote {output_csv}: {len(reference)} rows, {reference.shape[1]} columns "
          f"({n_with_tags} games carry tags).")


if __name__ == "__main__":
    merge()
