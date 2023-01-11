import numpy as np
import pandas as pd
import SALib


NOT_SWEEPABLE = ['_capex_alpha', '_VOM_alpha', '_FOM_alpha']


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


def scale_random_seed(v, a=1, b=256):
    return a + np.floor(v * (b - a + 1))


def main():
    # read HERON model XML
    # generate points to sample
    bounds = {
        'NPP_capacity': [0.6, 1.0],
        'NPP_capex_alpha': [-1200e6, -1600e6],
        'NPP_FOM_alpha': [-41.6e6, -48.0e6],
        'NPP_VOM_alpha': [-6.6044e3, -8.2574e3],
        'BOP_capacity': [0.4, 0.7],
        'BOP_minimum': [0, 0.2],
        'BOP_capex_alpha': [-500e6, -700e6],
        'BOP_FOM_alpha': [-40e6, -60e6],
        'BOP_VOM_alpha': [0e3, -2e3],
        'TES_capacity': [1.0, 5.0],
        'TES_capex_alpha': [-1.929e6, -11.572e6],
        'TES_FOM_alpha': [-14.0e3,-43.0e3],
        'TES_VOM_alpha': [-3e3, -29e3],
        'TES_sqrt_rte': [0.4 ** 0.5, 0.93 ** 0.5],
        'random_seed': [0, 1.0]
    }
    # for opt_traj in [4, 8, 16, 32]:
    
    N = 256
    morris_points = generate_morris_points(bounds, N, num_levels=128)
    df = pd.DataFrame(morris_points, columns=list(bounds.keys()))
    df['random_seed'] = scale_random_seed(df['random_seed'], a=1, b=256)

    print(morris_points.shape)
    print(df['random_seed'].sort_values().unique())

    exit()

    df['PointProbability'] = np.ones(len(df))
    df['ProbabilityWeight'] = np.ones(len(df))
    df.to_csv(f'samples{len(df)}_rng.csv', index=False)
    """
    for opt_traj in [32]:
        N = 200
        morris_points = generate_morris_points(bounds, N, optimal_trajectories=opt_traj)
        df = pd.DataFrame(morris_points, columns=list(bounds.keys()))
        df['random_seed'] = scale_random_seed(df['random_seed'], a=1, b=256)

        print(df['random_seed'].sort_values().unique())
        exit()

        df['PointProbability'] = np.ones(len(df))
        df['ProbabilityWeight'] = np.ones(len(df))
        df.to_csv(f'samples{len(df)}_rng.csv', index=False)
    """


if __name__ == '__main__':
    main()
