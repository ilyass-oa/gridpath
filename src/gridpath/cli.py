"""Command-line solver; no display or interactive prompts required."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lle import World

from .problems import CornerProblem, ExitProblem, GemProblem
from .search import SearchLimitExceeded, astar, bfs, dfs


def positive(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Gridpath: graph search for grid-world puzzles.")
    source = result.add_mutually_exclusive_group()
    source.add_argument(
        "--level", type=int, choices=range(1, 7), help="built-in LLE level (default: 1)"
    )
    source.add_argument("--map", type=Path, help="UTF-8 map file; use - for standard input")
    result.add_argument("--algorithm", choices=["astar", "bfs", "dfs"], default="astar")
    result.add_argument("--problem", choices=["exit", "gems", "corners"], default="exit")
    result.add_argument(
        "--max-expanded", type=positive, default=100000, help="expansion budget (default: 100000)"
    )
    result.add_argument("--json", action="store_true", help="emit a JSON result")
    return result


def load_world(path: Path | None, level: int | None) -> World:
    if path is None:
        world = World.level(level or 1)
    else:
        limit = 1024 * 1024
        if str(path) == "-":
            data = sys.stdin.buffer.read(limit + 1)
        else:
            if not path.is_file():
                raise ValueError(f"Not a regular map file: {path}")
            with path.open("rb") as stream:
                data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Map exceeds 1 MiB")
        text = data.decode("utf-8")
        if not text.strip():
            raise ValueError("Map is empty")
        world = World(text)
    world.seed(0)
    world.reset()
    return world


def main(argv: list[str] | None = None) -> int:
    arguments = parser()
    args = arguments.parse_args(argv)
    try:
        world = load_world(args.map, args.level)
        problem = {"exit": ExitProblem, "gems": GemProblem, "corners": CornerProblem}[args.problem](
            world
        )
        search = {"astar": astar, "bfs": bfs, "dfs": dfs}[args.algorithm]
        result = search(problem, max_expanded=args.max_expanded)
        if result is None:
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": "unreachable",
                            "algorithm": args.algorithm,
                            "problem": args.problem,
                        }
                    )
                )
            else:
                print("No solution.")
            return 1
        actions = [
            [move.name for move in (step if isinstance(step, tuple) else (step,))]
            for step in result.actions
        ]
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "solved",
                        "algorithm": args.algorithm,
                        "problem": args.problem,
                        "steps": result.n_steps,
                        "expanded": result.expanded,
                        "actions": actions,
                    }
                )
            )
        else:
            print(f"Solved in {result.n_steps} steps ({result.expanded} expanded states).")
            for index, moves in enumerate(actions, 1):
                print(f"{index}: " + ", ".join(moves))
        return 0
    except SearchLimitExceeded as error:
        if args.json:
            print(json.dumps({"status": "limit_reached", "message": str(error)}))
        else:
            print(str(error), file=sys.stderr)
        return 3
    except (OSError, ValueError, RuntimeError, UnicodeError) as error:
        arguments.exit(2, f"Error: {error}\n")
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
