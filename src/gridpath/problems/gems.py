from lle import World, WorldState

from .base import manhattan
from .exit import ExitProblem


class GemProblem(ExitProblem):
    """Collect every gem, then get every agent to an exit alive."""

    def __init__(self, world: World):
        super().__init__(world)
        self.gem_positions = tuple(gem.pos for gem in world.gems)

    def is_goal_state(self, state: WorldState) -> bool:
        return all(state.gems_collected) and super().is_goal_state(state)

    def heuristic(self, state: WorldState) -> float:
        remaining = (
            pos for pos, collected in zip(self.gem_positions, state.gems_collected) if not collected
        )
        # Each remaining gem needs some agent to reach it; ignore obstacles.
        gem_bound = max(
            (min(manhattan(agent, gem) for agent in state.agents_positions) for gem in remaining),
            default=0,
        )
        return max(float(gem_bound), self.exit_bound(state))
