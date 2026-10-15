from __future__ import annotations

from collections.abc import Hashable, Iterator
from dataclasses import dataclass

from lle import World, WorldState

from .base import Move, SearchProblem, manhattan
from .exit import ExitProblem


@dataclass(frozen=True, slots=True)
class CornerState:
    world_state: WorldState
    visited_corners: frozenset[tuple[int, int]]


class CornerProblem(SearchProblem[CornerState]):
    """Visit every grid corner collectively, then reach exits alive."""

    def __init__(self, world: World):
        self.world = world
        self._exit = ExitProblem(world)
        self.corners = frozenset(
            {
                (0, 0),
                (0, world.width - 1),
                (world.height - 1, 0),
                (world.height - 1, world.width - 1),
            }
        )
        base = self._exit.initial_state
        self._initial_state = CornerState(base, self.corners.intersection(base.agents_positions))

    @property
    def initial_state(self) -> CornerState:
        return self._initial_state

    def state_key(self, state: CornerState) -> Hashable:
        return self._exit.state_key(state.world_state), state.visited_corners

    def is_goal_state(self, state: CornerState) -> bool:
        return state.visited_corners == self.corners and self._exit.is_goal_state(state.world_state)

    def get_successors(self, state: CornerState) -> Iterator[tuple[CornerState, Move]]:
        for successor, move in self._exit.get_successors(state.world_state):
            visited = state.visited_corners | self.corners.intersection(successor.agents_positions)
            yield CornerState(successor, visited), move

    def heuristic(self, state: CornerState) -> float:
        positions = state.world_state.agents_positions
        remaining = self.corners - state.visited_corners
        corner_bound = max(
            (min(manhattan(pos, corner) for pos in positions) for corner in remaining), default=0
        )
        return max(float(corner_bound), self._exit.heuristic(state.world_state))
