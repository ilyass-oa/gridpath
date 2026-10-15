"""Unit-cost graph searches, independent of the simulation's mutable world."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from typing import Generic, TypeVar

from .priority_queue import PriorityQueue
from .problems import Move, SearchProblem

S = TypeVar("S")


class SearchLimitExceeded(RuntimeError):
    """The explicit expansion budget was exhausted, not proven unsolvable."""


@dataclass(slots=True, eq=False)
class SearchNode(Generic[S]):
    state: S
    parent: SearchNode[S] | None = None
    prev_action: Move | None = None
    cost: int = 0


@dataclass(slots=True)
class Solution(Generic[S]):
    actions: list[Move]
    states: list[S]
    expanded: int = 0

    @property
    def n_steps(self) -> int:
        return len(self.actions)

    @staticmethod
    def from_node(node: SearchNode[S], expanded: int = 0) -> Solution[S]:
        actions: list[Move] = []
        states: list[S] = []
        while True:
            states.append(node.state)
            if node.parent is None:
                break
            assert node.prev_action is not None
            actions.append(node.prev_action)
            node = node.parent
        return Solution(list(reversed(actions)), list(reversed(states)), expanded)


class _Budget:
    def __init__(self, limit: int | None):
        if limit is not None and (
            isinstance(limit, bool) or not isinstance(limit, int) or limit < 1
        ):
            raise ValueError("max_expanded must be a positive integer or None")
        self.limit = limit
        self.expanded = 0

    def visit(self) -> None:
        if self.limit is not None and self.expanded >= self.limit:
            raise SearchLimitExceeded(f"Search stopped after {self.expanded} expanded states")
        self.expanded += 1


def _uninformed(
    problem: SearchProblem[S], depth_first: bool, max_expanded: int | None
) -> Solution[S] | None:
    budget = _Budget(max_expanded)
    root = SearchNode(problem.initial_state)
    frontier = deque([root])
    visited = {problem.state_key(root.state)}
    while frontier:
        node = frontier.pop() if depth_first else frontier.popleft()
        if problem.is_goal_state(node.state):
            return Solution.from_node(node, budget.expanded)
        budget.visit()
        for state, action in problem.get_successors(node.state):
            key = problem.state_key(state)
            if key not in visited:
                visited.add(key)
                frontier.append(SearchNode(state, node, action, node.cost + 1))
    return None


def dfs(problem: SearchProblem[S], *, max_expanded: int | None = None) -> Solution[S] | None:
    """Find a reachable goal using a stack; the path need not be shortest."""
    return _uninformed(problem, True, max_expanded)


def bfs(problem: SearchProblem[S], *, max_expanded: int | None = None) -> Solution[S] | None:
    """Find a shortest path when each transition costs one step."""
    return _uninformed(problem, False, max_expanded)


def _heuristic(problem: SearchProblem[S], state: S) -> float:
    value = float(problem.heuristic(state))
    if not isfinite(value) or value < 0:
        raise ValueError("Heuristic must be finite and nonnegative")
    return value


def astar(problem: SearchProblem[S], *, max_expanded: int | None = None) -> Solution[S] | None:
    """Find a shortest path with an admissible heuristic, reopening improved states."""
    budget = _Budget(max_expanded)
    root = SearchNode(problem.initial_state)
    frontier: PriorityQueue[SearchNode[S]] = PriorityQueue()
    frontier.push(root, _heuristic(problem, root.state))
    best = {problem.state_key(root.state): 0}
    while not frontier.is_empty():
        node = frontier.pop()
        key = problem.state_key(node.state)
        # Skip stale entries, but permit a cheaper path to reopen an old state.
        if node.cost != best[key]:
            continue
        if problem.is_goal_state(node.state):
            return Solution.from_node(node, budget.expanded)
        budget.visit()
        for state, action in problem.get_successors(node.state):
            successor_key = problem.state_key(state)
            cost = node.cost + 1
            if cost < best.get(successor_key, float("inf")):
                best[successor_key] = cost
                frontier.push(
                    SearchNode(state, node, action, cost), cost + _heuristic(problem, state)
                )
    return None
