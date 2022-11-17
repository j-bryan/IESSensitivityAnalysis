import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main(ISO, qty):
    data = pd.read_csv(f'{ISO}/{ISO}_2021.csv', index_col=0)
    plt.plot(data[qty])
    plt.show()


if __name__ == '__main__':
    main('CAISO', 'SOLAR')
