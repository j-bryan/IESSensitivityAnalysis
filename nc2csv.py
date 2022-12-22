import sys
import os
import xarray as xr
import pandas as pd


def read_netcdf(pth):
    ds = xr.open_dataset(pth)
    df = ds.to_dataframe()
    return df


def write_df(df, pth):
    df.to_csv(pth)


if __name__ == '__main__':
    for filename in sys.argv[1:]:
        data = read_netcdf(filename)
        for c, d in data.groupby('_ROM_Cluster'):
            head, tail = os.path.split(filename)
            name, ext = os.path.splitext(tail)
            newfilename = name + '_' + str(c) + '.csv'
            csv_pth = os.path.join(head, newfilename)
            write_df(d, csv_pth)

