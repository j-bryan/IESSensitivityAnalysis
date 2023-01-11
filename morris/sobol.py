import numpy as np
import pandas as pd
import SALib


def generate_sobol_points(bounds, N, **kwargs):
    problem = build_problem(bounds)
    from SALib.sample import sobol
    points = sobol.sample(problem, N)
    return points


def build_problem(bounds):
    var_names = list(bounds.keys())
    var_bounds = list(bounds.values())
    for i, b in enumerate(var_bounds):
        var_bounds[i] = sorted(b)
    problem = {
        'num_vars': len(var_names),
        'names': var_names,
        'bounds': var_bounds
    }
    return problem


def scale_random_seed(v, a=1, b=256):
    return a + np.floor(v * (b - a + 1))


def sample(bounds):
    N = 4
    points = generate_sobol_points(bounds, N)
    df = pd.DataFrame(points, columns=list(bounds.keys()))
    df['random_seed'] = scale_random_seed(df['random_seed'], a=1, b=512)
    df.to_csv('sobol_samples.csv')


def analyze(bounds):
    problem = build_problem(bounds)
    data = pd.read_csv('MISO_Sobol_o/sweep.csv')
    inputs = pd.read_csv('sobol_samples.csv', index_col=0)
    df = inputs.merge(data)
    
    print(data.head())
    print(inputs.head())
    print(df.head())
    #npv = data['mean_NPV'].to_numpy()

    #from SALib.analyze import sobol
    #Si = sobol.analyze(problem, npv, parallel=True, n_processors=64)
    #print(Si)


def compare_runs():
    df1 = pd.read_csv('MISO_Sobol_o/sweep.csv')
    df2 = pd.read_csv('MISO_Sobol_o_copy/sweep.csv')

    df1 = df1.rename(columns={'mean_NPV': 'NPV1'})
    df2 = df2.rename(columns={'mean_NPV': 'NPV2'})

    cols_to_drop = []
    for col in list(df1.columns):
        if '_NPV' in col or 'Probability' in col:
            cols_to_drop.append(col)

    df1 = df1.drop(columns=cols_to_drop)
    df2 = df2.drop(columns=cols_to_drop)

    df = df1.merge(df2)
    print(df)


def main():
    BOUNDS = {
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
    # sample(BOUNDS)
    # analyze(BOUNDS)
    compare_runs()



if __name__ == '__main__':
    main()

