import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def quantile_plot(region, value, normalize=True):
    axis_labels = {
        'PRICE': 'DAM Electricity Price',
        'TOTALLOAD': 'DAM Total Load',
        'WIND': 'Wind Power (normalized)',
        'SOLAR': 'Solar Power (normalized)'
    }
    ylims = {
        'PRICE': [0, 3],
        'TOTALLOAD': [0.5, 1.5],
        'WIND': [0, 1],
        'SOLAR': [0, 1]
    }

    data = pd.read_csv(f'ARMA/{region}/Data_0.csv', index_col=0)
    prices = data[value].to_numpy().reshape((len(data) // 24, 24))

    if normalize:
        for i in range(len(prices)):
            prices[i] /= np.mean(prices[i])

    fig, ax = plt.subplots()

    colors = ['#f4ccd4', '#c0a7cf', '#568ad6', '#082c62']
    quantiles = [(2, 98), (10, 90), (35, 65)]
    for i, (lq, hq) in enumerate(quantiles):
        lq_vals = np.quantile(prices, lq / 100, axis=0)
        hq_vals = np.quantile(prices, hq / 100, axis=0)
        ax.fill_between(np.arange(24), hq_vals, lq_vals, color=colors[i], label=f'P{lq}-P{hq}')

    median = np.median(prices, axis=0)
    ax.plot(np.arange(24), median, color=colors[-1], linewidth=3, label='Median')

    ylabel = axis_labels.get(value)
    if normalize:
        ylabel += ' (normalized)'
    ax.set_ylabel(ylabel)
    ax.set_xlim([0, 23])
    ax.set_xticks([0, 4, 8, 12, 16, 20])
    ax.set_xticklabels(['0:00', '4:00', '8:00', '12:00', '16:00', '20:00'])

    ylim = ylims.get(value)
    ticks_dx = 0.5 if ylim[1] - ylim[0] > 1 else 0.25
    ticks = np.arange(ylim[0], ylim[1] + ticks_dx, ticks_dx)
    tick_labels = [f'{int(tick * 100)}%' for tick in ticks]
    ax.set_ylim(ylim)
    ax.set_yticks(ticks)
    ax.set_yticklabels(tick_labels)

    ax.grid(which='major', axis='y')
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_title(f'{region}, 2021')

    # ax.legend(loc='lower right')
    ax.legend()
    # plt.show()
    plt.savefig(f'figures/{value.lower()}-variability-{region}-2021.png', dpi=200)


if __name__ == '__main__':
    for REGION in ['ERCOT', 'CAISO', 'MISO']:
        for VALUE in  ['PRICE', 'TOTALLOAD', 'WIND', 'SOLAR']:
            norm = VALUE in ['PRICE', 'TOTALLOAD']
            quantile_plot(REGION, VALUE, normalize=norm)
