"""
Load the merged ``gdco_data.csv`` and reconstruct the two dataframes the Games
Mapper pipeline expects:

    tags      : long DataFrame with columns [nb, tag, appid] (one row per game-tag),
                identical to the old ``gdco_tags.csv``.
    reference : the original ``gdco_reference.csv`` columns (one row per appid).

This lets the pipeline read a single source file while staying byte-for-byte
equivalent to the previous two-file setup (gdco_reference.csv + gdco_tags.csv).
"""
import json

import pandas as pd

DEFAULT_PATH = "data/gdco_data.csv"

# Columns added by merge_gdco_data.py on top of the reference table.
_ARRAY_COLUMNS = ["tags", "tagCounts"]


def load_gdco_data(path=DEFAULT_PATH):
    """Return ``(tags, reference)`` reconstructed from the merged ``gdco_data.csv``."""
    data = pd.read_csv(path, low_memory=False)

    # reference = the original reference columns, untouched.
    reference = data.drop(columns=_ARRAY_COLUMNS)

    # tags = explode the aligned JSON arrays back into long (nb, tag, appid) rows.
    exploded = data.drop_duplicates(subset="appid")[["appid"] + _ARRAY_COLUMNS].copy()
    exploded["tags"] = exploded["tags"].apply(json.loads)
    exploded["tagCounts"] = exploded["tagCounts"].apply(json.loads)
    exploded = exploded.explode(_ARRAY_COLUMNS, ignore_index=True)
    exploded = exploded.dropna(subset=["tags"])  # drop games that carried no tags

    tags = pd.DataFrame({
        "nb": exploded["tagCounts"].astype(int).to_numpy(),
        "tag": exploded["tags"].astype(str).to_numpy(),
        "appid": exploded["appid"].astype(int).to_numpy(),
    })

    return tags, reference
