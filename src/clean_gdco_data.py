"""
Produce ``data/gdco_simulation.csv``: the case-study dataset — a small, shareable
subset of ``gdco_data.csv`` keeping exactly the games the Games Mapper Simulation
study clusters:

  * at least 100 reviews,
  * released between 2015 and 2025 (inclusive), and
  * tagged "Simulation" with tag priority >= 0.6 (i.e. Simulation is a dominant tag),
    using the same gdco tag-vote data and priority = nb / max(nb) the pipeline uses.

Duplicate game names are first collapsed to a single row (first occurrence) on the
full catalogue, exactly as ``MapperDataPreparation._clean_reference_data`` does, so the
surviving games are precisely the ones the pipeline selects. The clustering output on
``gdco_simulation.csv`` is therefore identical to a run on the full ``gdco_data.csv``
(verified for the Simulation case study).

The schema is unchanged: every column, including the ``tags`` / ``tagCounts`` arrays,
is carried over as-is. Run from the repository root:

    python ./src/clean_gdco_data.py
"""
import json

import pandas as pd

INPUT_CSV = "data/gdco_data.csv"
OUTPUT_CSV = "data/gdco_simulation.csv"
MIN_REVIEWS = 100
MIN_YEAR = 2015
MAX_YEAR = 2025
TAG = "Simulation"
PRIORITY_THRESHOLD = 0.6


def _tag_priority(tags_json, counts_json, tag=TAG):
    """Replicate the pipeline's priority = nb / max(nb) for `tag`; -1 if the tag is absent."""
    tags = json.loads(tags_json)
    if tag not in tags:
        return -1.0
    counts = json.loads(counts_json)
    top = max(counts) if counts else 0
    if top <= 0:
        return -1.0
    return counts[tags.index(tag)] / top


def clean(input_csv=INPUT_CSV, output_csv=OUTPUT_CSV):
    df = pd.read_csv(input_csv, low_memory=False)
    n_in = len(df)

    # Mirror MapperDataPreparation._clean_reference_data: collapse duplicate game
    # names (first occurrence) on the full catalogue, BEFORE filtering.
    df = df.groupby("name", as_index=False).first()

    # Year, parsed exactly like the pipeline (9999-12-31 is the missing-date placeholder).
    release = df["releaseDate"].replace(["9999-12-31"], pd.NA)
    year = pd.to_datetime(release, errors="coerce").dt.year

    # Simulation tag priority, computed from the tags/tagCounts arrays exactly as the
    # pipeline computes it from the gdco tag-vote data.
    priority = pd.Series(
        [_tag_priority(t, c) for t, c in zip(df["tags"], df["tagCounts"])],
        index=df.index,
    )

    keep = (
        (df["reviewCount"] >= MIN_REVIEWS)
        & year.between(MIN_YEAR, MAX_YEAR)
        & (priority >= PRIORITY_THRESHOLD)
    )
    cleaned = df[keep]

    cleaned.to_csv(output_csv, index=False)
    print(f"{input_csv}: {n_in} games -> {output_csv}: {len(cleaned)} games "
          f"({len(cleaned) / n_in:.2%} of catalogue).")


if __name__ == "__main__":
    clean()
