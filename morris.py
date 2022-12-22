import numpy as np
import SALib


NOT_SWEEPABLE = ['_capex', '_VOM', '_FOM']


def generate_morris_points(bounds, N, **kwargs):
    var_names = list(bounds.keys())
    var_bounds = list(bounds.values())
    for i, b in enumerate(var_bounds):
        var_bounds[i] = sorted(b)
    problem = {
        'num_vars': len(var_names),
        'names': var_names,
        'bounds': var_bounds
    }
    from SALib.sample import morris
    points = morris.sample(problem, N, optimal_trajectories=kwargs.get('optimal_trajectories', 4))
    # grouped = group_points(points, problem)
    # return grouped
    return points


def group_points(pts, problem):
    # We can group the Morris sample points into the minimum number of files by finding those which have the same
    # NOT_SWEEPABLE parameters.
    not_sweepable = []
    for i, var_name in enumerate(problem['names']):
        for ns in NOT_SWEEPABLE:
            if ns in var_name:
                not_sweepable.append(i)
                break
    unique_econ_params = np.unique(pts[:, not_sweepable], axis=0)
    groups = []
    for i, row in enumerate(unique_econ_params):
        groups.append(pts[np.isclose(pts[:, not_sweepable], row).all(axis=1)])
    return groups


def build_heron_xmls():
    # build file with all NOT_SWEEPABLE parameters set as fixed values, all others set as sweeps

    pass


def main():
    # read HERON model XML
    # generate points to sample
    bounds = {  # TODO use len=1 to indicate a <fixed_parameter> instead of <sweep_values>?
        'NPP_capacity': [0.6, 1.0],
        'NPP_capex': [-1140, -1520],
        'NPP_FOM': [-104, -120],
        'NPP_VOM': [-6.6044, -8.2574],
        'BOP_capacity': [0.4, 0.7],
        'BOP_minimum': [0, 0.4],
        'BOP_capex': [-500, -700],
        'BOP_FOM': [-40, -60],
        'BOP_VOM': [0, -2],
        'TES_capacity': [1.5, 5.0],
        'TES_capex': [-1.7, -10.3],
        'TES_FOM': [-14, -43],
        'TES_VOM': [-3, -29],
        'TES_RTE': [0.4, 0.93]
    }
    N = 200
    opt_traj = 32
    morris_points = generate_morris_points(bounds, N, optimal_trajectories=opt_traj)
    print(morris_points.shape)


if __name__ == '__main__':
    main()
