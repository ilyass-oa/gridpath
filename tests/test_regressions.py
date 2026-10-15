from lle import Action, World

from gridpath.problems import CornerProblem, ExitProblem
from gridpath.search import astar


class GraphState:
    def __init__(self, name):
        self.name = name
        self.agents_positions = [(name, 0)]
        self.gems_collected = []
        self.agents_alive = [True]


class InconsistentGraph:
    """Unit edges with an admissible, inconsistent lower bound at B."""

    initial_state = GraphState("S")
    world = World("S0 X")
    edges = {"S": ["A", "B"], "A": ["C"], "C": ["X"], "B": ["X"], "X": ["Y"], "Y": ["G"], "G": []}

    def state_key(self, state):
        return state.name

    def get_successors(self, state):
        return [(GraphState(name), Action.EAST) for name in self.edges[state.name]]

    def is_goal_state(self, state):
        return state.name == "G"

    def heuristic(self, state):
        return 3 if state.name == "B" else 0


def test_astar_reopens_cheaper_states():
    solution = astar(InconsistentGraph())
    assert solution is not None
    assert solution.n_steps == 4


def test_joint_actions_move_every_agent():
    problem = ExitProblem(World("S0 . X\nS1 . X"))
    solution = astar(problem)
    assert solution is not None
    assert solution.n_steps == 2
    problem.world.reset()
    for actions in solution.actions:
        problem.world.step(actions)
    assert problem.is_goal_state(problem.world.get_state())


def test_successors_preserve_current_world_state():
    problem = ExitProblem(World("S0 . . X\n. . . ."))
    initial = problem.initial_state
    problem.world.step(Action.SOUTH)
    problem.world.step(Action.EAST)
    current = problem.world.get_state()
    list(problem.get_successors(initial))
    assert problem.world.get_state() == current


def test_initial_corner_counts_as_visited():
    problem = CornerProblem(World("S0 . X\n. . ."))
    assert (0, 0) in problem.initial_state.visited_corners


def test_joint_step_heuristic_does_not_sum_agent_distances():
    problem = ExitProblem(World("S0 . X\nS1 . X"))
    assert problem.heuristic(problem.initial_state) <= 2
