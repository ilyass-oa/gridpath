from gridpath.problems import CornerProblem, ExitProblem, GemProblem
from gridpath.search import Solution

IMPOSSIBLE = """
S0 . . @ X
.  . . @ @
.  . . . .
.  . . . ."""

EMPTY = """
S0 . . . . . . . . . . .
.  . . . . . . . . . . .
.  . . . . . . . . . . .
.  . . . . . . . . . . .
.  . . . . . . . . . . X
"""

ZIGZAG = """
.  . . @ . . . @ . X
.  @ . @ . @ . @ . @
S0 @ . . . @ . . . @
"""


GEMS = """
G  G @ G  @ @
G  . . S0 G .
@  @ G .  . G
G  . @ G  G .
G  . @ .  G X
.  . G G  G X"""


def check_exit_problem(problem: ExitProblem, solution: Solution):
    world = problem.world
    world.reset()
    for action in solution.actions:
        world.step(action)
    state = world.get_state()
    assert all(state.agents_alive), "The agent is dead"
    assert all(pos in world.exit_pos for pos in state.agents_positions), (
        "The agent did not reach the exit"
    )


def check_corner_problem(problem: CornerProblem, solution: Solution):
    world = problem.world
    world.set_state(problem.initial_state.world_state)
    corners = set(problem.corners) - set(world.agents_positions)
    for action in solution.actions:
        world.step(action)
        agent_pos = world.agents_positions[0]
        if agent_pos in corners:
            corners.remove(agent_pos)
    assert len(corners) == 0, f"The agent did not reach these corners: {corners}"
    assert world.agents_positions[0] in world.exit_pos, "The agent did not reach the exit"


def check_gem_problem(problem: GemProblem, solution: Solution):
    world = problem.world
    world.reset()
    for action in solution.actions:
        world.step(action)
    state = world.get_state()
    assert all(state.gems_collected), "Not all gems have been collected"
    assert all(state.agents_alive), "The agent is dead"
    assert all(pos in world.exit_pos for pos in state.agents_positions)
