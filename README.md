# Gridpath

DFS, BFS and A* for grid-world puzzles built with [Laser Learning Environment](https://github.com/yamoling/lle). Agents navigate obstacles and lasers, collect gems and reach exits. Several agents can move together in one search step.

## Run

Requires Python 3.12 or 3.13 with pip and venv. Tested on Linux.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e '.[dev]'

gridpath --map examples/gems.txt --problem gems
gridpath --map examples/cooperative.txt --problem gems --json
```

Choose `--algorithm astar`, `bfs` or `dfs`. Objectives are `exit`, `gems` and `corners`. Use `--level 1` for a built-in map, or `--map -` to read a map from standard input. `python -m gridpath` works too.

```sh
gridpath --map examples/lasers.txt --max-expanded 10000
```

## Search behavior

BFS finds the fewest simultaneous steps. A* does the same with the supplied lower-bound heuristics and reopens states when it finds a shorter route. DFS finds a path without guaranteeing its length.

The corner objective counts starting corners and visits by every agent. Search preserves the world's current state, and returned paths can be replayed. The CLI stops after 100,000 expanded states by default; large joint state spaces can still be expensive.

## Tests

```sh
pytest
ruff check .
ruff format --check .
```

See [search details](docs/search.md) for the Python API, heuristics and exit codes.
