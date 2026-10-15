# Search model

Each edge costs one simultaneous world step. A move is an LLE `Action` for one agent, or a tuple of actions ordered by agent index for several agents. Movement, laser blocking, collisions and exits follow the rules of [LLE 2.6.1](https://pypi.org/project/laser-learning-environment/2.6.1/).

## Objectives and states

- `ExitProblem`: every agent reaches an exit alive.
- `GemProblem`: collect all gems and satisfy the exit objective.
- `CornerProblem`: visit all four geometric grid corners collectively, then satisfy the exit objective. A corner occupied initially already counts. Duplicate corners on a one-row/column map count once. A blocked corner makes this objective unreachable.

Problem construction snapshots the current world state. Successor generation restores the world before yielding, including when stepping raises an error. Dead successors are excluded. State keys include positions, gem collection and agent health; corner keys also include visited corners. Keep the map layout fixed during a search and use separate worlds for concurrent searches.

```python
from lle import World
from gridpath import ExitProblem, astar

world = World('S0 . X')
world.reset()
problem = ExitProblem(world)
solution = astar(problem, max_expanded=10000)
if solution is not None:
    for action in solution.actions:
        world.step(action)
```

`Solution.states` contains the initial state followed by the state after each action. `n_steps` counts joint moves; `expanded` counts non-goal nodes whose successors were requested. `None` means the reachable graph was exhausted. `SearchLimitExceeded` means the expansion budget was reached.

## Algorithms and heuristics

DFS uses a stack and does not guarantee a shortest path. BFS uses a FIFO queue and marks states when discovered. A* keeps the best known path cost, skips stale queue entries and permits cheaper paths to reopen previously expanded states. Equal priorities preserve insertion order.

A* requires a finite, nonnegative, admissible heuristic for its shortest-path guarantee. The supplied estimates ignore obstacles and use Manhattan distance:

- Exit: maximum, across agents, of distance to the nearest exit.
- Gems: maximum of the exit bound and each remaining gem's distance from its nearest agent.
- Corners: maximum of the exit bound and each unvisited corner's distance from its nearest agent.

These are lower bounds because agents move at most one cell per joint step. Summing independent agents' distances can overestimate concurrent work. Tests compare A* with BFS on generated maps and on graphs with admissible but inconsistent heuristics.

The state space grows with agents, gems and corner history. `max_expanded` limits node expansion, rather than elapsed time or memory. The CLI also limits map text to 1 MiB. Dependencies are pinned in `requirements.lock`; the simulator is an external library.

## CLI exit codes

| Code | Meaning |
| --- | --- |
| 0 | Solved, or help displayed |
| 1 | No reachable solution |
| 2 | Invalid arguments, map or runtime input |
| 3 | Expansion budget reached |
| 130 | Interrupted with Ctrl+C |

`--json` produces a machine-readable search result with status, actions and step count. Argument and file errors are reported on stderr. The CLI runs without a display.
