"""
Custom Dispatcher for 2021 LWRS FPOG Milestone studying the effects of
different storage technologies in the NYISO market.

Modified by Jacob Bryan for use with the Natrium system
"""
from functools import partial

import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Global Constants
ECONV_RATE = 0.4
HEAT_TECHS = ['TES']

# This is what the NYISO stack looks like:
#                                            capacity_gw     marginal_cost
# NY    Reference    Storage    Solar        14.289311       0.000000
#                               Wind         10.435570       0.000000
#                               Hydro         4.277016       0.000000
#                               Nuclear       1.143500      12.689066
#                               NGCC          4.533380      25.109150
#                               NGGT         17.224408      32.703513
#                               Overflow     35.000000     169.679554
#                    No_Storage Solar        14.894274       0.000000
#                               Wind         10.435570       0.000000
#                               Hydro         4.277016       0.000000
#                               Nuclear       1.143500      12.689066
#                               NGCC          4.533380      25.109150
#                               NGGT         14.524706      32.703513
#                               Overflow     35.000000     169.679554
#       CES          Storage    Solar         9.774715       0.000000
#                               Wind         11.881870       0.000000
#                               Hydro         4.277016       0.000000
#                               Nuclear       5.242805      12.689066
#                               NGCC          2.101907      25.109150
#                               NGGT          4.638107      32.703513
#                               Overflow     35.000000     169.679554
#                    No_Storage Solar         9.774715       0.000000
#                               Wind         11.881869       0.000000
#                               Hydro         4.277016       0.000000
#                               Nuclear       5.242805      12.689066
#                               NGCC          2.101907      25.109150
#                               NGGT          2.101907      32.703513
#                               Overflow     35.000000     169.679554

# 'coeffs' taken from exponential fit formulas computed in
# ../../scripts/cap_cost_proc.py script
# CASE_DICT = {('Reference', 'No_Storage'): {'coeffs': (12.791, 0.025),
#                                            'windcap': 10.435570,
#                                            'solarcap': 14.894274,
#                                            'nucap': 1.143500},
#
#               ('Reference', 'Storage'):    {'coeffs': (12.881, 0.026),
#                                             'windcap': 10.435570,
#                                             'solarcap': 14.289311,
#                                             'nucap': 1.143500},
#
#               ('CES', 'No_Storage'):       {'coeffs': (12.403, 0.032),
#                                             'windcap': 11.881869,
#                                             'solarcap': 9.774715,
#                                             'nucap': 5.242805},
#
#               ('CES', 'Storage'):          {'coeffs': (12.791, 0.034),
#                                             'windcap': 9.774715,
#                                             'solarcap': 11.881870,
#                                             'nucap': 5.242805}}
CASE_DICT = {
    'MISO': {'coeffs': (5.8535, 0.02245),  # exponential fit to all (load, price) points for 2021
             'windcap': 31.098,  # from Form EIA-680, 2021
             'solarcap': 3.839,  # from Form EIA-680, 2021
             'nucap': 25.407},  # from Form EIA-680, 2021
    'CAISO': {'coeffs': (12.881, 0.026),  # TODO: these are carried over from EPRI for NYISO!
             'windcap': 6.188,  # from Form EIA-680, 2021
             'solarcap': 15.568,  # from Form EIA-680, 2021
             'nucap': 2.323},  # from Form EIA-680, 2021
    'ERCOT': {'coeffs': (12.881, 0.026),  # TODO: these are carried over from EPRI for NYISO!
             'windcap': 34.173,  # from ERCOT "Hourly Aggregated Wind and Solar Output" (https://www.ercot.com/mp/data-products/data-product-details?id=PG7-126-M)
             'solarcap': 9.323,  # from ERCOT "Hourly Aggregated Wind and Solar Output" (https://www.ercot.com/mp/data-products/data-product-details?id=PG7-126-M)
             'nucap': 5.1386}  # from Form EIA-680, 2021
}


def dispatch(info, activity_matrix):
    """
    Dispatches the components based on user-defined algorithms.
    The expected return object is a dict of components, mapped to a dict of
      resources that component uses, mapped to the amount consumed/produced
      as a numpy array.
    Note:
     - Negative values mean the component consumes that resource
     - Positive values mean the component produces that resource
     - The activity doesn't necessarily have to be as long as "time", but it usually should be
    @ In, info, dict, information about the state of the system
    @ Out, activity, dict, activity of components as described above
    """
    heron = info['HERON']
    case = info['HERON']['Case']
    components = dict((c.name, c) for c in heron['Components'])
    sources = heron['Sources']
    labels = heron['Case'].get_labels()
    label_id = labels['region']

    # Grab wind/solar capacity and wind/solar generation
    wind_cap = CASE_DICT[labels['region']]['windcap']
    solar_cap = CASE_DICT[labels['region']]['solarcap']
    wind_pct = heron['RAVEN_vars']['WIND']
    solar_pct = heron['RAVEN_vars']['SOLAR']
    total_load = heron['RAVEN_vars']['TOTALLOAD']
    clearing_price = heron['RAVEN_vars']['PRICE']
    wind = wind_pct * wind_cap
    solar = solar_pct * solar_cap
    # This is the net load after removing VREs
    load = total_load - wind - solar
    load[load < 0] = 0 # Curtail VRE Sources

    # Since ARMA resolution is by hour we hold this constant
    time_dt = 1
    T = len(load)
    storage_dat = dict(
        (name, {
            'initial_level': float(components[name].get_interaction().get_initial_level(info)),
            'capacity': components[name].get_capacity(info)[0][components[name].get_interaction().get_resource()],
            'component': components[name],
            'RTE': float(components[name].get_sqrt_RTE())
        }) for name in HEAT_TECHS)

    ###
    # PYOMO MODEL
    ###
    m = pyo.ConcreteModel()
    Ts = np.arange(0, T, dtype=int)
    m.T = pyo.Set(initialize=Ts)
    m.Load = load
    m.ClearingPrice = clearing_price
    m.StorageDat = storage_dat
    m.Labels = label_id

    # Components: Nuclear, BOPs, TES, Grid
    m.NPP = components['NPP'].get_capacity(info)[0]['heat']
    # m.NPP_unused = pyo.Var(m.T, within=pyo.NonPositiveReals, initialize=0)

    BOP_min = components['BOP'].get_minimum(info)[0]['electricity']
    BOP_max = components['BOP'].get_capacity(info)[0]['electricity']

    m.BOP = pyo.Var(m.T,
                    within=pyo.NonNegativeReals,
                    bounds=(BOP_min, BOP_max),
                    initialize=BOP_min)
    BOP_interaction = components['BOP'].get_interaction()
    BOP_transfer_coeffs = BOP_interaction.get_transfer().get_coefficients()
    BOP_inputs = list(BOP_interaction.get_inputs())
    BOP_outputs = list(BOP_interaction.get_outputs())
    if len(BOP_inputs) != 1 or len(BOP_outputs) != 1:
        raise ValueError("idk what to do with this BOP model given")
    m.BOP_efficiency = abs(BOP_transfer_coeffs[BOP_outputs[0]] / BOP_transfer_coeffs[BOP_inputs[0]])

    m.Other = pyo.Var(m.T,
                      within=pyo.NonNegativeReals,
                      bounds=(0, max(load) * 1.1), # Upper Bound is > leftover load
                      initialize=0)

    # Create 3 pyomo vars for each storage component
    for tes in HEAT_TECHS:
        cap = storage_dat[tes]['capacity']
        level = pyo.Var(m.T,
                        within=pyo.NonNegativeReals,
                        bounds=(0, cap),
                        initialize=0)
        charge = pyo.Var(m.T,
                         within=pyo.NonPositiveReals,
                         bounds=(-cap / (2.09 * time_dt), 0),  # TODO: need to dynamically change these bounds
                         initialize=0)
        discharge = pyo.Var(m.T,
                            within=pyo.NonNegativeReals,
                            bounds=(0, cap / (5.5 * time_dt)),  # TODO: need to dynamically change these bounds
                            initialize=0)
        setattr(m, f'{tes}_level', level)
        setattr(m, f'{tes}_charge', charge)
        setattr(m, f'{tes}_discharge', discharge)

    # Conservation Contraint Functions
    m.EConserve = pyo.Constraint(m.T, rule=_conserve_elec)
    m.HConserve = pyo.Constraint(m.T, rule=_conserve_heat)

    # Clean H2 Constraints (Used in Tax Credit Case)
    # m.CleanH = pyo.Constraint(m.T, rule=_clean_h2)

    # Transfer Functions
    for tech in HEAT_TECHS:
        func = partial(_storage_mgmt_level, tech)
        setattr(m, f'{tech}_mgmt_level', pyo.Constraint(m.T, rule=func))

    # Objective Function
    m.OBJ = pyo.Objective(sense=pyo.maximize, rule=_objective)

    m.pprint()
    soln = pyo.SolverFactory('ipopt').solve(m)
    if soln.solver.status == SolverStatus.ok and soln.solver.termination_condition == TerminationCondition.optimal:
        print('Successful optimization solve.')
        debug_pyomo_soln(m)
    else:
        print('Storage optimization FAILURE!')
        print(' ... status:', soln.solver.status)
        print(' ... termination:', soln.solver.termination_condition)

        import logging
        from pyomo.util.infeasible import log_infeasible_constraints
        logging.basicConfig(filename='dereg_dispatch_pyomo.log', level=logging.DEBUG)
        logger = logging.getLogger()
        log_infeasible_constraints(m, logger=logger)
        # with open('log.txt', 'w') as f:
        #     f.write(log_infeasible_constraints(m))

        m.pprint()
        raise RuntimeError('Failed solve!')

    # store activity
    # NOTE for SecM and E_dump we directly include prices here rather than recalculate them in TEAL,
    #      since we have the load data now and won't have it (as accessible) then.
    for htech in HEAT_TECHS:
        for trackr in ['level', 'charge', 'discharge']:
            activity_matrix.set_activity_vector(
                components[htech],
                'heat',
                np.array(list(getattr(m, f'{htech}_{trackr}')[t].value for t in m.T)),
                tracker=trackr
            )

    # 'grid_sales' is electricity sold to grid coming from NPP, Electrical Storage, Thermal Storage.
    # However, the BOP output already incorporates elec from the NPP and Thermal Storage, so we just
    # need to gather the electricity from Electrical Storage.
    activity_matrix.set_activity_vector(components['NPP'], 'heat', np.ones(len(m.T)) * m.NPP)
    # activity_matrix.set_activity_vector(components['NPP_unused'], 'heat', [m.NPP_unused[t].value for t in m.T])
    BOP_elec = np.array(list(m.BOP[t].value for t in m.T))
    activity_matrix.set_activity_vector(components['BOP'], 'electricity', BOP_elec)
    activity_matrix.set_activity_vector(components['BOP'], 'heat', -BOP_elec / m.BOP_efficiency)

    # We flip the sign because grid_sales should be all positive and grid is consuming.
    activity_matrix.set_activity_vector(components['grid'], 'electricity', -BOP_elec)

    return activity_matrix


def _objective(m):
    """
    TODO
    """
    total = 0
    for t in m.T:
        total += m.ClearingPrice[t] * m.BOP[t]
    return total


def _storage_mgmt_level(name, m, t):
    """
    TODO
    """
    level = getattr(m, f'{name}_level')
    charge = getattr(m, f'{name}_charge')
    discharge = getattr(m, f'{name}_discharge')
    if t > 0:
        prev = level[t-1]
    else:
        prev = m.StorageDat[name]['initial_level']
    sqrt_rte = m.StorageDat[name]['RTE']
    prod = (-sqrt_rte * charge[t]) - (discharge[t] / sqrt_rte)
    # we multiply by dt here but it's 1 always
    return level[t] == prev + prod * 1


def _conserve_elec(m, t):
    """
    TODO
    """
    sources = m.BOP[t] + m.Other[t]
    sinks = -m.Load[t]
    battery = 0
    return sources + battery + sinks == 0


def _conserve_heat(m, t):
    """
    TODO
    """
    sources = m.NPP
    sinks = -1 * m.BOP[t] / m.BOP_efficiency
    battery = 0
    for tes in HEAT_TECHS:
        charge = getattr(m, f'{tes}_charge')[t]
        discharge = getattr(m, f'{tes}_discharge')[t]
        battery += (charge + discharge)
    return sources + battery + sinks == 0


def debug_pyomo_print(m):
    print('/' + '='*80)
    print('DEBUGG model pieces:')
    print('  -> objective:')
    print('     ', m.objective.pprint())
    print('  -> variables:')
    for var in m.component_objects(pyo.Var):
        print('     ', var.pprint())
        print('  -> constraints:')
    for constr in m.component_objects(pyo.Constraint):
        print('     ', constr.pprint())
        print('\\' + '='*80)
        print('')


def debug_pyomo_soln(m):
    print('DEBUGG solution:')
    print('  -> objective:', m.OBJ())
    print('t: ' + ', '.join(f'{var.name:9s}' for var in m.component_objects(pyo.Var)))
    for t in m.T:
        msg = f'{t}: '
        for var in m.component_objects(pyo.Var):
            msg += f'{var[t].value:1.3e}, '
            print(msg)


def debug_setup_print(activity, m, stack, prices, comp_order, load,
                      htse_cap_h2, npp_cap, store_cap, store_initial, market_cap,
                      price_h2_kg, price_h2_GW, NPP_bid, H2_opp, bid_adjust):
    print('DEBUGG capacities:')
    print(f'  -> npp (GW): {npp_cap:1.2e}')
    print(f'  -> store (kgH2): {store_cap:1.2e}')
    print(f'  -> store initial (kgH2): {store_initial:1.2e}')
    print(f'  -> market (kgH2/s): {market_cap:1.2e}')
    print('DEBUGG conversion/costs:')
    print(f'  -> H2 price ($/kg/s): {price_h2_kg:1.2e}')
    print(f'  -> H2_opp ($/GW): {H2_opp:1.2e}')
    print(f'  -> NPP bid adjust ($/GW): {float(bid_adjust):1.2e}')
    print(f'  -> NPP TOTAL bid ($/GW): {float(NPP_bid):1.2e}')
    print('DEBUGG activity:')
    print('  t: load(GW), NPP->grid(GW)') #, htse(H2/s), store(H2)')
    template = '  {t}: {load:1.2e}, {grid:1.2e}' #, {htse:1.2e}, {store:1.2e}'
    for t in range(len(load)):
        print(template.format(t=t, load=load[t],
                              # npp=activity['NPP']['electricity'][t],
                              grid=activity['grid']['electricity'][t],
                              # htse=activity['HTSE']['H2'][t],
                              # store=activity['H2_storage']['H2'][t],
                              ))
        print('DEBUGG stack:')
        print('  i: stack, price, comp')
        for i in range(len(stack)):
            print(f'  {i}: {stack[i]:1.2e}, {prices[i]:1.2e}, {comp_order[i]}')
