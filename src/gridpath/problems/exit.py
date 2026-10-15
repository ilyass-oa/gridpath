from lle import WorldState

from .base import WorldProblem


class ExitProblem(WorldProblem):
    """Every agent must reach an exit alive."""

    def is_goal_state(self, state: WorldState) -> bool:
        return all(state.agents_alive) and all(pos in self.exits for pos in state.agents_positions)

    def heuristic(self, state: WorldState) -> float:
        return self.exit_bound(state)
