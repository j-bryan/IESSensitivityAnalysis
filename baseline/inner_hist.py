import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def monthly_avg():
    fig, ax = plt.subplots(nrows=3, ncols=1)
    months = np.array([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
    months = months.cumsum()
    for i, region in enumerate(['CAISO', 'MISO', 'ERCOT']):
        historical = pd.read_csv(f'../ARMA/{region}/{region}_2021.csv', index_col=0)
        price = historical['PRICE'].to_numpy()
        # monthly_prices = [price[months[j]:months[j+1]] for j in range(len(months) - 1)]
        # ax[i].boxplot(monthly_prices)
        monthly_means = [price[months[j]:months[j+1]].mean() for j in range(len(months) - 1)]
        ax[i].bar(np.arange(1, 13), monthly_means)
        ax[i].ticklabel_format(axis='y', style='sci', scilimits=(0, 0), useMathText=True)
    plt.tight_layout()
    plt.show()
    # plt.savefig('daily_price.png', dpi=200)


def hourly_avg():
    fig, ax = plt.subplots(nrows=3, ncols=1)
    for i, region in enumerate(['CAISO', 'MISO', 'ERCOT']):
        historical = pd.read_csv(f'../ARMA/{region}/{region}_2021.csv', index_col=0)
        price = historical['PRICE'].to_numpy()
        hourly_prices = price.reshape((365, 24))
        ax[i].boxplot(hourly_prices)
        ax[i].ticklabel_format(axis='y', style='sci', scilimits=(0, 0), useMathText=True)
    plt.tight_layout()
    plt.show()
    # plt.savefig('daily_price.png', dpi=200)


def npv_hist():
    fig, ax = plt.subplots(nrows=3, ncols=2)
    for i, region in enumerate(['CAISO', 'MISO', 'ERCOT']):
        historical = pd.read_csv(f'../ARMA/{region}/{region}_2021.csv', index_col=0)
        ax[i, 0].plot(historical['PRICE'])
        print(region, historical['PRICE'].mean())

        npv = pd.read_csv(f'TES/{region}/{region}_baseline_30yr_o/sweep/1/{region}_baseline_30yr_i/all_metrics.csv')['NPV']
        ax[i, 1].hist(npv)

        ax[i, 0].set_ylabel(f'{region}\nPrice ($/GWh)')
        ax[i, 0].ticklabel_format(axis='y', style='sci', scilimits=(0, 0), useMathText=True)
        ax[i, 1].ticklabel_format(axis='x', style='sci', scilimits=(0, 0), useMathText=True)

    ax[2, 0].set_xlabel('Time (h)')
    ax[2, 1].set_xlabel('NPV ($)')
    plt.tight_layout()
    # plt.show()
    plt.savefig('npv_hists.png', dpi=200)


if __name__ == '__main__':
    # npv_hist()
    # hourly_avg()
    monthly_avg()
