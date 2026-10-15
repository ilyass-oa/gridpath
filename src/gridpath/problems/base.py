"""Search contracts and side-effect-free transitions for LLE worlds."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterable, Iterator
from itertools import product
from typing import Generic, TypeVar

from lle import Action, World, WorldState
from lle.exceptions import InvalidActionError

S = TypeVar("S")
type Move = Action | tuple[Action, ...]


class SearchProblem(ABC, Generic[S]):
    @property
    @abstractmethod
    def initial_state(self) -> S:
        """The state from which a search starts."""

    @abstractmethod
    def state_key(self, state: S) -> Hashable:
        """An immutable key containing every part of the search state."""

    @abstractmethod
    def is_goal_state(self, state: S) -> bool:
        """Whether the objective has been reached."""

    @abstractmethod
    def get_successors(self, state: S) -> Iterable[tuple[S, Move]]:
        """Valid transitions, each costing one simultaneous world step."""

    def heuristic(self, state: S) -> float:
        """A nonnegative lower bound on remaining steps; zero is always safe."""
        return 0.0


class WorldProblem(SearchProblem[WorldState], ABC):
    def __init__(self, world: World):
        self.world = world
        self._initial_state = world.get_state()
        self.exits = frozenset(world.exit_pos)

    @property
    def initial_state(self) -> WorldState:
        return self._initial_state

    def state_key(self, state: WorldState) -> Hashable:
        return (
            tuple(state.agents_positions),
            tuple(state.gems_collected),
            tuple(state.agents_alive),
        )

    def get_successors(self, state: WorldState) -> Iterator[tuple[WorldState, Move]]:
        if not all(state.agents_alive):
            return
        previous = self.world.get_state()
        try:
            self.world.set_state(state)
            choices = self.world.available_actions()
        finally:
            self.world.set_state(previous)

        # Iterate joint choices lazily: eagerly building 5**n actions is costly.
        for joint in product(*choices):
            try:
                self.world.set_state(state)
                self.world.step(joint)
                successor = self.world.get_state()
            except InvalidActionError:
                continue
            finally:
                # Restore before yielding, even if the caller stops iteration.
                self.world.set_state(previous)
            if all(successor.agents_alive):
                move = joint[0] if len(joint) == 1 else joint
                yield successor, move

    def exit_bound(self, state: WorldState) -> float:
        if not self.exits:
            return 0.0
        # Agents move simultaneously, so summing their distances overestimates.
        return float(
            max(
                (
                    min(manhattan(pos, exit_pos) for exit_pos in self.exits)
                    for pos in state.agents_positions
                ),
                default=0,
            )
        )


def manhattan(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])
