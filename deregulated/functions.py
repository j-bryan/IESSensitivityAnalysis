import numpy as np
import pandas as pd


def _build_stack(df):
    stacked = df.sort_values('marginal_cost', ascending=True)
    stack = stacked['capacity_gw'].to_numpy().cumsum()
    prices = stacked['marginal_cost'].to_numpy()
    return stack, prices


def _clearing_price(load, stack, prices):
    i = np.searchsorted(stack, load)
    return prices[i], i


def get_load(data, meta):
    """
    Acquires the electric load
    Might be reducable to just the ARMA
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
    """
    load = meta['HERON']['RAVEN_vars']['TOTALLOAD']
    t = meta['HERON']['time_index']
    return {'electricity': load[t]}, meta


def grid_price(data, meta):
    """
    Determines the clearing price of electricity.
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
    """
    data = {
        'component': ['Hydro', 'Nuclear', 'NGCC', 'NGGT', 'Overflow'],
        'marginal_cost': [0.0, 12.689066, 25.109150, 32.703513, 169.679554],
        'capacity_gw': [4.277016, 1.143500, 4.533380, 17.224408, 35.000000]
    }
    df = pd.DataFrame(data)

    t = meta['HERON']['time_index']
    for comp in meta['HERON']['Components']:
        if comp.name == 'Additional_NPP':
            npp = comp
            break
    else:
        raise RuntimeError
    npp_activity_th = meta['HERON']['all_activity'].get_activity(npp, 'production', 'heat', t)
    npp_activity_e = npp_activity_th * 0.33  # TODO: get efficiency from BOP
    # get the load from the ARMA
    load_e = get_load(data, meta)[0]['electricity']
    # use the stack to derive the electricity price based on the load
    stack, prices = _build_stack(df)
    price, _ = _clearing_price(load_e, stack, prices)
    # Convert stack prices from $/MW to $/GW
    return {'reference_price': price * 1e3}, meta


# DEBUGG
if __name__ == '__main__':
    # Nothing to test here
    pass
