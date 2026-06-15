# Best of Steam

A self-contained study that clusters the games featured in Steam's yearly
**"Best of Steam"** lists (2019–2025), separately for *new releases* and *top sellers*,
and labels each cluster with its most salient tags.

## Provenance notebooks (Databricks)

These were exported from Databricks and are included for provenance. They are **not
runnable locally**: they rely on Pullup Entertainment's internal Spark tables
(`rnd_dev.silver.gdco_*`, `rnd_dev.gold.sonar_*`) and the internal `pullup-cluster` /
`steam-toolkit` packages.

| Notebook | Output |
| --- | --- |
| `Analysis - BOS new.py` | parses the "Best of" new-release lists → `bos_new_2019_2025.csv` |
| `Analysis - BOS sellers.py` | parses the "Best of" top-seller lists → `bos_sellers_2019_2025.csv` |
| `Clustering new.py` | clusters new releases → `clustering_best_new.csv`, `best_new.pkl` |
| `Clustering sellers.py` | clusters top sellers → `clustering_best_sellers.csv`, `best_sellers.pkl` |

## Local script

- `best_of_steam.py` — consumes the committed `clustering_best_*.csv` together with the
  shared `data/gdco_*.csv`, and names each yearly cluster via Cohen's *h* (reusing
  `src/utils.py`). Requires the `data/` files to be present (see
  [`../../data/README.md`](../../data/README.md)).

## Committed artefacts

The intermediate CSV and PKL outputs listed above are committed so the local script and
downstream inspection work without re-running the Databricks pipeline.
