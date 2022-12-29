import os
import sys
import pandas as pd


def aggregate_inner(case_name, path_to_case='.'):
    outer_dirpath = os.path.join(path_to_case, case_name + '_o')
    sweep_dirpath = os.path.join(outer_dirpath, 'sweep')

    inner_data = pd.DataFrame()

    for loc in os.listdir(sweep_dirpath):
        filepath = os.path.join(sweep_dirpath, loc, case_name + '_i', 'all_metrics.csv')
        if os.path.exists(filepath):
            inner_runs = pd.read_csv(filepath)
            inner_data[loc] = inner_runs['NPV']
            # inner_runs[loc] = inner_data
    
    inner_data.to_csv(os.path.join(outer_dirpath, 'allNPV.csv'))


if __name__ == '__main__':
    for loc in sys.argv[1:]:
        basepath, case_name = os.path.split(loc)
        aggregate_inner(case_name, basepath)
