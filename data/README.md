# Data

The Games Mapper pipeline reads two CSV files from this folder:

| File | Description |
| --- | --- |
| `gdco_reference.csv` | One row per Steam game (release reference data). |
| `gdco_tags.csv` | One row per *(game, tag)* pair (user-defined Steam tags). |

> **Note** — these files are **not committed** to the repository. `gdco_reference.csv`
> exceeds GitHub's 100 MB file-size limit, and the underlying data source is currently
> being updated. Place the two CSVs in this folder before running `src/main.py`.

## Expected schema

`gdco_reference.csv` — columns used by the code:

- `appid` — Steam application id (integer).
- `name` — game title.
- `releaseDate` — release date as `YYYY-MM-DD`. The placeholder `9999-12-31` denotes an
  unknown / unreleased date and is treated as missing.
- `reviewCount` — number of user reviews (used to filter games and to choose the titles
  shown when hovering a cluster).

`gdco_tags.csv` — columns used by the code:

- `appid` — Steam application id (matches `gdco_reference.csv`).
- `tag` — the Steam tag (e.g. `Simulation`, `Roguelike`, `Co-op`).
- `nb` — number of votes for that tag on that game.

The pipeline derives a per-game tag **priority** as `nb / max(nb)` across that game's
tags, and keeps a game under a tag when its priority is `>= 0.6`.
