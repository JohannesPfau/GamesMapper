# Data

The Games Mapper pipeline reads a single CSV from this folder. Two versions exist:

| File | Committed? | Contents |
| --- | --- | --- |
| `gdco_simulation.csv` | **yes** (~5.5 MB) | The case-study dataset the pipeline reads by default: the **4,996 Simulation games** the study clusters — tagged `Simulation` at priority ≥ 0.6, with ≥ 100 reviews, released 2015–2025. |
| `gdco_data.csv` | no (~150 MB) | The full catalogue (159k games). Needed for any other genre / wider scope, and to (re)build `gdco_simulation.csv`. |

> Both files share the **same schema** and either can be passed to
> `gdco_data.load_gdco_data(...)`. `src/main.py` points at `gdco_simulation.csv`; for
> other genres or a wider scope, point `path_data` there at `data/gdco_data.csv`.

## Schema

One row per game (`appid`). Every column of the original Steam reference export is kept;
the columns used by the code are:

- `appid` — Steam application id (integer).
- `name` — game title.
- `releaseDate` — `YYYY-MM-DD`; the placeholder `9999-12-31` denotes an unknown /
  unreleased date and is treated as missing.
- `reviewCount` — number of user reviews.
- `tags` — JSON array of the game's Steam tags, e.g. `["Simulation", "Strategy", "Indie"]`.
- `tagCounts` — JSON array of player counts, **aligned** with `tags` so `tagCounts[i]` is
  the number of players who applied `tags[i]`.

`src/gdco_data.py` reconstructs the two dataframes the pipeline works with: a long
*(nb, tag, appid)* `tags` table and the wide `reference` table. The per-game tag
**priority** is `nb / max(nb)` across that game's tags; a game is kept under a tag when
that priority is `>= 0.6`.

## Build chain

```
gdco_reference.csv  +  gdco_tags.csv        (raw exports, not committed)
        |   python ./src/merge_gdco_data.py
        v
   gdco_data.csv                            full catalogue, not committed (~150 MB)
        |   python ./src/clean_gdco_data.py
        v
   gdco_simulation.csv                      committed case-study subset (~5.5 MB) — pipeline input
```

`clean_gdco_data.py` collapses duplicate game names (first occurrence) exactly as the
pipeline does, then keeps games with ≥ 100 reviews released 2015–2025 that carry the
`Simulation` tag at priority ≥ 0.6 — i.e. precisely the games the case study clusters.
This makes the clustering output on `gdco_simulation.csv` identical to a run on the full
`gdco_data.csv` (verified).
