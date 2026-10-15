"""Graph and simulator checks beyond the original coursework examples."""

import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import pytest
from lle import Action, World, WorldState

from gridpath import CornerProblem, ExitProblem, GemProblem, SearchLimitExceeded, astar, bfs, dfs
from gridpath.priority_queue import PriorityQueue
from tests.test_regressions import InconsistentGraph

SEARCHES = [dfs, bfs, astar]


def replay(problem, solution):
    root = solution.states[0]
    problem.world.set_state(getattr(root, "world_state", root))
    assert len(solution.states) == solution.n_steps + 1
    for action, expected in zip(solution.actions, solution.states[1:]):
        problem.world.step(action)
        assert problem.world.get_state() == getattr(expected, "world_state", expected)
    assert problem.is_goal_state(solution.states[-1])


@pytest.mark.parametrize("search", SEARCHES)
@pytest.mark.parametrize("problem_type", [ExitProblem, GemProblem, CornerProblem])
def test_search_is_repeatable_and_preserves_world(search, problem_type):
    world = World("S0 . G\n. . X")
    problem = problem_type(world)
    before = world.get_state()
    first = search(problem)
    assert first is not None
    assert world.get_state() == before
    second = search(problem)
    assert second is not None
    assert second.actions == first.actions
    assert second.states == first.states
    assert world.get_state() == before
    replay(problem, first)


@pytest.mark.parametrize("search", SEARCHES)
def test_search_from_current_state_and_zero_move_goal(search):
    world = World("S0 G . X")
    world.reset()
    world.step(Action.EAST)
    before = world.get_state()
    problem = GemProblem(world)
    assert problem.initial_state == before
    result = search(problem)
    assert result is not None and result.n_steps == 2
    assert world.get_state() == before
    world.set_state(result.states[-1])
    goal = GemProblem(world)
    empty = search(goal)
    assert empty is not None and empty.n_steps == 0
    assert len(empty.states) == 1
    assert world.get_state() == goal.initial_state


@pytest.mark.parametrize("search", SEARCHES)
def test_budget_is_explicit_and_keeps_world_unchanged(search):
    problem = ExitProblem(World("S0 . . X"))
    before = problem.world.get_state()
    with pytest.raises(SearchLimitExceeded):
        search(problem, max_expanded=1)
    assert problem.world.get_state() == before
    for invalid in (0, -1, 1.5, True):
        with pytest.raises(ValueError, match="max_expanded"):
            search(problem, max_expanded=invalid)


def test_partial_successor_iteration_and_errors_restore_state():
    world = World("S0 G . X")
    problem = GemProblem(world)
    world.step(Action.EAST)
    before = world.get_state()
    iterator = problem.get_successors(problem.initial_state)
    next(iterator)
    assert world.get_state() == before
    iterator.close()
    assert world.get_state() == before
    with pytest.raises(IndexError):
        list(problem.get_successors(WorldState([(999, 999)], [False])))
    assert world.get_state() == before

    class BrokenStep:
        def __getattr__(self, name):
            return getattr(world, name)

        def step(self, actions):
            world.step(actions)
            raise RuntimeError("step failed after mutation")

    problem.world = BrokenStep()
    with pytest.raises(RuntimeError, match="after mutation"):
        list(problem.get_successors(problem.initial_state))
    assert world.get_state() == before


def test_keys_include_gems_health_and_corner_history():
    problem = GemProblem(World("S0 G X"))
    variants = [
        WorldState([(0, 0)], [False], [True]),
        WorldState([(0, 0)], [True], [True]),
        WorldState([(0, 0)], [False], [False]),
    ]
    assert len({problem.state_key(state) for state in variants}) == 3
    corners = CornerProblem(World("S0 . X\n. . ."))
    start = corners.initial_state
    changed = type(start)(start.world_state, frozenset())
    assert corners.state_key(start) != corners.state_key(changed)


@pytest.mark.parametrize("search", SEARCHES)
def test_dead_successors_are_filtered_and_dead_starts_fail(search):
    problem = ExitProblem(World("S0 V X"))
    assert all(
        all(state.agents_alive) for state, _ in problem.get_successors(problem.initial_state)
    )
    assert search(problem) is None
    problem.world.step(Action.EAST)
    dead = ExitProblem(problem.world)
    assert list(dead.get_successors(dead.initial_state)) == []
    assert search(dead) is None


def test_every_agent_can_visit_a_corner():
    problem = CornerProblem(World("S0 X\nS1 X"))
    assert problem.initial_state.visited_corners == frozenset({(0, 0), (1, 0)})
    states = list(problem.get_successors(problem.initial_state))
    right = next(state for state, actions in states if actions == (Action.STAY, Action.EAST))
    assert (1, 1) in right.visited_corners
    result = astar(problem)
    assert result is not None and result.n_steps == 1
    replay(problem, result)


def test_laser_cooperation_is_solved_and_replayable():
    map_text = (Path(__file__).resolve().parents[1] / "examples/lasers.txt").read_text()
    problem = ExitProblem(World(map_text))
    before = problem.world.get_state()
    shortest = bfs(problem)
    informed = astar(problem)
    assert shortest is not None and informed is not None
    assert informed.n_steps == shortest.n_steps == 4
    assert problem.world.get_state() == before
    replay(problem, informed)
    assert all(agent.is_alive and agent.has_arrived for agent in problem.world.agents)


def test_three_agent_joint_path():
    problem = GemProblem(World("S0 G X\nS1 . X\nS2 . X"))
    result = astar(problem)
    assert result is not None and result.n_steps == 2
    assert all(len(move) == 3 for move in result.actions)
    replay(problem, result)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1])
def test_astar_rejects_invalid_heuristics(bad):
    problem = InconsistentGraph()
    problem.heuristic = lambda state: bad
    with pytest.raises(ValueError, match="Heuristic"):
        astar(problem)


def test_stable_priority_queue_does_not_compare_items():
    first, second, earlier = object(), object(), object()
    queue = PriorityQueue()
    queue.push(first, 1)
    queue.push(second, 1)
    queue.push(earlier, 0)
    assert [queue.pop(), queue.pop(), queue.pop()] == [earlier, first, second]
    assert queue.is_empty()
    with pytest.raises(IndexError):
        queue.pop()
    for bad in (float("inf"), float("nan")):
        with pytest.raises(ValueError, match="finite"):
            queue.push(first, bad)


@dataclass(frozen=True)
class IntegerGraph:
    edges: tuple[tuple[int, ...], ...]
    lower_bounds: tuple[int, ...]
    initial_state: int = 0

    def state_key(self, state):
        return state

    def is_goal_state(self, state):
        return state == len(self.edges) - 1

    def get_successors(self, state):
        return [(neighbor, Action.STAY) for neighbor in self.edges[state]]

    def heuristic(self, state):
        return self.lower_bounds[state]


def test_astar_matches_bfs_on_admissible_inconsistent_graphs():
    rng = random.Random(284)
    reopened = False
    for _ in range(80):
        size = rng.randrange(4, 15)
        edges = tuple(
            tuple(target for target in range(size) if rng.random() < 0.22) for _ in range(size)
        )
        reverse = [[] for _ in range(size)]
        for source, targets in enumerate(edges):
            for target in targets:
                reverse[target].append(source)
        distance = {size - 1: 0}
        queue = deque([size - 1])
        while queue:
            target = queue.popleft()
            for source in reverse[target]:
                if source not in distance:
                    distance[source] = distance[target] + 1
                    queue.append(source)
        heuristic = tuple(rng.randrange(distance.get(node, 0) + 1) for node in range(size))
        reopened |= any(
            heuristic[source] > 1 + heuristic[target]
            for source, targets in enumerate(edges)
            for target in targets
        )
        problem = IntegerGraph(edges, heuristic)
        expected, actual = bfs(problem), astar(problem)
        assert (expected is None) == (actual is None)
        if actual is not None:
            assert expected.n_steps == actual.n_steps == distance[0]
            assert actual.states[0] == 0 and actual.states[-1] == size - 1
            for source, target in zip(actual.states, actual.states[1:]):
                assert target in edges[source]
    assert reopened, "The deterministic sample must include inconsistent heuristics"


@pytest.mark.parametrize("problem_type", [ExitProblem, GemProblem, CornerProblem])
def test_heuristics_and_astar_against_bfs_on_small_maps(problem_type):
    rng = random.Random(501)
    for _ in range(12):
        rows = [["." for _ in range(4)] for _ in range(3)]
        for row in range(3):
            for col in range(4):
                if rng.random() < 0.15:
                    rows[row][col] = "@"
        rows[0][0], rows[2][3] = "S0", "X"
        if problem_type is GemProblem:
            rows[1][1], rows[2][0] = "G", "G"
        problem = problem_type(World("\n".join(" ".join(row) for row in rows)))
        expected = bfs(problem)
        actual = astar(problem)
        assert (actual is None) == (expected is None)
        if actual is not None:
            assert actual.n_steps == expected.n_steps
            assert problem.heuristic(problem.initial_state) <= actual.n_steps
            assert problem.heuristic(actual.states[-1]) == 0
            replay(problem, actual)
