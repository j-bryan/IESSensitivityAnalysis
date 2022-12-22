import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def main():
    base = 'dispatches'
    for f in os.listdir(base):
        if not f.endswith('.csv'):
            continue
        pth = os.path.join(base, f)
        data = pd.read_csv(pth)
        bop_out = data['Dispatch__BOP__production__electricity'].to_numpy()
        is_max = np.argwhere(bop_out == 0.5)
        if len(is_max) / len(bop_out) > 0.3:
            print(f)


if __name__ == '__main__':
    main()

