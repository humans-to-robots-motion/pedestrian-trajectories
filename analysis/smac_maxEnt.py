import common_import
import logging

import numpy as np
from ConfigSpace.hyperparameters import *
from my_learning.max_ent import *
from my_utils.output_analysis import *

# Import ConfigSpace and different types of parameters
from smac.configspace import ConfigurationSpace
from smac.facade.smac_hpo_facade import SMAC4HPO
# Import SMAC-utilities
from smac.scenario.scenario import Scenario


# Run maxEnt
def maxEnt(x):
    nb_points = 40
    nb_rbfs = 5
    sigma = 0.1
    nb_samples = 100

    workspace = Workspace()

    w, original_costmap, starts, targets, paths = \
        create_random_environment(nb_points, nb_rbfs, sigma, nb_samples,
                                  workspace)

    centers = workspace.box.meshgrid_points(nb_rbfs)

    # Learn costmap
    a = MaxEnt(nb_points, centers, sigma, paths, starts, targets, workspace)
    # Set hyperparameters
    a._N = x["N"]
    a._learning_rate = x["learning rate"]
    a._stepsize_scalar = x["step size scalar"]

    learned_map, w_t = a.solve()
    # Calculate Training loss
    _, _, optimal_paths = plan_paths(nb_samples, learned_map[-1],
                                     workspace, starts=starts,
                                     targets=targets)
    loss = get_maxEnt_loss(learned_map[-1], paths, nb_points, w_t[-1])
    if loss < 0:
        loss = sys.maxsize
    return loss


logging.basicConfig(level=logging.INFO)  # logging.DEBUG for debug output

# Build Configuration Space which defines all parameters and their ranges
cs = ConfigurationSpace()
N = UniformIntegerHyperparameter("N", 20, 200, default_value=65)
learning_rate = UniformFloatHyperparameter("learning rate", 0.1, 2.0,
                                           default_value=0.7)
step_size_scalar = UniformIntegerHyperparameter("step size scalar", 1, 20,
                                                default_value=20)
cs.add_hyperparameters([N, learning_rate, step_size_scalar])

# Scenario object
scenario = Scenario({"run_obj": "quality",  # we optimize quality
                     # (alternatively runtime)
                     "runcount-limit": 5000,
                     "cs": cs,  # configuration space
                     "deterministic": "false",
                     "shared_model": True,
                     "input_psmac_dirs": "smac-output-maxEnt",
                     "cutoff_time": 9000,
                     "wallclock_limit": 'inf'
                     })

# Example call of the function
# It returns: Status, Cost, Runtime, Additional Infos
def_value = maxEnt(cs.get_default_configuration())
print("Default Value: %.2f" % def_value)

# Optimize, using a SMAC-object
print("Optimizing! Depending on your machine, this might take a few minutes.")
smac = SMAC4HPO(scenario=scenario,
                rng=np.random.RandomState(42),
                tae_runner=maxEnt)

# Start optimization
try:
    incumbent = smac.optimize()
finally:
    incumbent = smac.solver.incumbent

# inc_value = smac.get_tae_runner().run(incumbent, 1)[1]
# print("Optimized Value: %.2f" % inc_value)