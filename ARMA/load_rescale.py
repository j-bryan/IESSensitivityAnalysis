import pandas as pd


if __name__ == '__main__':
    for ISO in ['CAISO', 'ERCOT', 'MISO']:
        path = f'{ISO}/{ISO}_2021.csv'
        data = pd.read_csv(path, index_col=0)
        data['PRICE'] *= 1e3
        data.to_csv(path)
