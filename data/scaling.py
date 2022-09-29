import pandas as pd


def rescale_totalload(fpath):
    csv = pd.read_csv(fpath)
    csv['TOTALLOAD'] *= 1e-3
    csv.to_csv(fpath)


if __name__ == '__main__':
    rescale_totalload('../arma_train/Output/Data_0.csv')
