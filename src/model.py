import os

import oemof.solph as solph
import pandas as pd
from oemof.solph import views
from pyomo.contrib import appsi


class EnergySystem():
    """Model class that builds the energy system from parameters."""

    def __init__(self, data, param_units, param_opt):
        self.data = data
        self.param_units = param_units
        self.param_opt = param_opt

        self.tes_used = 'tes' in self.param_units.keys()
        self.chp_used = (
            ('ice' in self.param_units.keys())
            or ('ccet' in self.param_units.keys())
            )

        self.periods = len(data.index)
        self.es = solph.EnergySystem(
            timeindex=pd.date_range(
                data.index[0], periods=self.periods, freq='h'
                ),
            infer_last_interval=True
            )

        self.bwsf = calc_bwsf(
            self.param_opt['capital_interest'],
            self.param_opt['lifetime']
            )

        self.buses = {}
        self.comps = {}

    def generate_buses(self):
        self.buses['gnw'] = solph.Bus(label='gas network')
        self.buses['enw'] = solph.Bus(label='electricity network')
        self.buses['hnw'] = solph.Bus(label='heat network')
        self.buses['chp_node'] = solph.Bus(label='chp node')

        self.es.add(*list(self.buses.values()))

    def generate_sources(self):
        self.comps['gas_source'] = solph.components.Source(
            label='gas source',
            outputs={
                self.buses['gnw']: solph.flows.Flow(
                    variable_costs=(
                        self.data['gas_price']
                        + (self.data['co2_price'] * self.param_opt['ef_gas'])
                        )
                    )
                }
            )

        self.comps['elec_source'] = solph.components.Source(
            label='electricity source',
            outputs={
                self.buses['enw']: solph.flows.Flow(
                    variable_costs=(
                        self.param_opt['elec_consumer_charges_grid']
                        - self.param_opt['elec_consumer_charges_self']
                        + self.data['el_spot_price']
                        )
                    )
                }
            )

        self.es.add(self.comps['gas_source'], self.comps['elec_source'])

        if 'sol' in self.param_units.keys():
            self.comps['solar_source'] = solph.components.Source(
                label='solar thermal',
                outputs={
                    self.buses['hnw']: solph.flows.Flow(
                        variable_costs=self.param_units['sol']['op_cost_var'],
                        nominal_value=solph.Investment(
                            ep_costs=(
                                self.param_units['sol']['inv_spez']
                                / self.bwsf
                                ),
                            maximum=self.param_units['sol']['A_max'],
                            minimum=self.param_units['sol']['A_min']
                            ),
                        fix=self.data['solar_heat_flow']
                        )
                    }
                )

            self.es.add(self.comps['solar_source'])

    def generate_sinks(self):

        self.comps['heat_sink'] = solph.components.Sink(
            label='heat demand',
            inputs={
                self.buses['hnw']: solph.flows.Flow(
                    variable_costs=-self.param_opt['heat_price'],
                    nominal_value=self.data['heat_demand'].max(),
                    fix=self.data['heat_demand']/self.data['heat_demand'].max()
                    )
                }
            )

        self.comps['elec_sink'] = solph.components.Sink(
            label='spotmarket',
            inputs={
                self.buses['chp_node']: solph.flows.Flow(
                    variable_costs=(
                        -self.data['el_spot_price'] - self.param_opt['vNNE']
                        )
                    )
                }
            )

        self.es.add(self.comps['heat_sink'], self.comps['elec_sink'])

    def generate_components(self):
        internal_el = False
        for unit in self.param_units.keys():
            if unit in ['ccet', 'ice']:
                self.comps[unit] = solph.components.Converter(
                    label=unit,
                    inputs={self.buses['gnw']: solph.flows.Flow()},
                    outputs={
                        self.buses['chp_node']: solph.flows.Flow(
                            variable_costs=self.param_units[unit]['op_cost_var']
                            ),
                        self.buses['hnw']: solph.flows.Flow(
                            investment=solph.Investment(
                                ep_costs=(
                                    self.param_units[unit]['inv_spez']
                                    / self.bwsf
                                    ),
                                maximum=self.param_units[unit]['cap_max'],
                                minimum=self.param_units[unit]['cap_min']
                                ),
                            max=self.param_units[unit]['Q_rel_max'],
                            min=self.param_units[unit]['Q_rel_min'],
                            nonconvex=solph.NonConvex()
                            )
                        },
                    conversion_factors={
                        self.buses['chp_node']: self.param_units[unit]['eta_el'],
                        self.buses['hnw']: self.param_units[unit]['eta_th']
                        }
                    )

                self.es.add(self.comps[unit])
                internal_el = True

            if unit in ['hp', 'plb', 'eb']:
                if unit == 'hp':
                    eff = 'cop'
                    input_nw = 'enw'
                    var_cost = (
                        self.param_units[unit]['op_cost_var']
                        + self.param_opt['elec_consumer_charges_self']
                        )
                elif unit == 'plb':
                    eff = 'eta'
                    input_nw = 'gnw'
                    var_cost = (
                        self.param_units[unit]['op_cost_var']
                        + self.param_opt['energy_tax']
                        )
                elif unit == 'eb':
                    eff = 'eta'
                    input_nw = 'enw'
                    var_cost = (
                        self.param_units[unit]['op_cost_var']
                        + self.param_opt['elec_consumer_charges_self']
                        )

                self.comps[unit] = solph.components.Converter(
                    label=unit,
                    inputs={self.buses[input_nw]: solph.flows.Flow()},
                    outputs={
                        self.buses['hnw']: solph.flows.Flow(
                            investment=solph.Investment(
                                ep_costs=(
                                    self.param_units[unit]['inv_spez']
                                    / self.bwsf
                                    ),
                                maximum=self.param_units[unit]['cap_max'],
                                minimum=self.param_units[unit]['cap_min']
                                ),
                            max=self.param_units[unit]['Q_rel_max'],
                            min=self.param_units[unit]['Q_rel_min'],
                            nonconvex=solph.NonConvex(),
                            variable_costs=var_cost
                            )
                        },
                    conversion_factors={
                        self.buses[input_nw]: self.param_units[unit][eff]
                        }
                    )

                self.es.add(self.comps[unit])

            if unit == 'tes':
                self.comps[unit] = solph.components.GenericStorage(
                    label=unit,
                    investment=solph.Investment(
                        ep_costs=(
                            self.param_units[unit]['inv_spez'] / self.bwsf
                            ),
                        maximum=self.param_units[unit]['Q_max'],
                        minimum=self.param_units[unit]['Q_min']
                        ),
                    inputs={
                        self.buses['hnw']: solph.flows.Flow(
                            variable_costs=self.param_units[unit]['op_cost_var']
                            )
                        },
                    outputs={
                        self.buses['hnw']: solph.flows.Flow(
                            variable_costs=self.param_units[unit]['op_cost_var']
                            )
                        },
                    invest_relation_input_capacity=(
                        self.param_units[unit]['Q_in_to_cap']
                        ),
                    invest_relation_output_capacity=(
                        self.param_units[unit]['Q_out_to_cap']
                        ),
                    initial_storage_level=self.param_units[unit]['init_storage'],
                    loss_rate=self.param_units[unit]['Q_rel_loss'],
                    balanced=self.param_units[unit]['balanced']
                    )

                self.es.add(self.comps[unit])

        if internal_el:
            self.comps['chp_internal'] = solph.components.Converter(
                label='chp internal',
                inputs={self.buses['chp_node']: solph.flows.Flow()},
                outputs={self.buses['enw']: solph.flows.Flow(
                    nominal_value=9999,
                    max=1.0,
                    min=0.0
                    )},
                conversion_factors={self.buses['enw']: 1}
                )

            self.es.add(self.comps['chp_internal'])

    def solve_model(self):
        self.model = solph.Model(self.es)
        if self.param_opt['Solver'] == 'Gurobi':
            solver = 'gurobi'
            gapname = 'MIPGap'
            self.model.solve(
                solver=solver, solve_kwargs={'tee': True},
                cmdline_options={gapname: self.param_opt['MIPGap']}
                )
        elif self.param_opt['Solver'] == 'HiGHS':
            solver = 'highs'
            gapname = 'mip_rel_gap'
            opt = appsi.solvers.Highs()
            opt.config.mip_gap = self.param_opt['MIPGap']
            opt.config.logfile = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'highs_log.txt'
                ))
            # opt.config.stream_solver = True
            # opt.highs_options['output_flag'] = True
            # opt.highs_options['log_to_console'] = True
            opt.solve(self.model)

    def get_results(self):
        self.results = solph.processing.results(self.model)
        # breakpoint()
        # self.meta_results = solph.processing.meta_results(self.model)

        data_gnw = views.node(self.results, 'gas network')['sequences']
        data_enw = views.node(self.results, 'electricity network')['sequences']
        data_hnw = views.node(self.results, 'heat network')['sequences']

        if self.chp_used:
            data_chpnode = views.node(self.results, 'chp node')['sequences']

        data_hnw_caps = views.node(self.results, 'heat network')['scalars']

        if self.tes_used:
            data_tes = views.node(self.results, 'tes')['sequences']
            data_tes_cap = views.node(self.results, 'tes')['scalars'][
                (('tes', 'None'), 'invest')
                ]

        # Combine all data and relabel the column names
        self.data_all = pd.concat([data_gnw, data_enw, data_hnw], axis=1)
        if self.tes_used:
            self.data_all = pd.concat([self.data_all, data_tes], axis=1)
        if self.chp_used:
            self.data_all = pd.concat([self.data_all, data_chpnode], axis=1)
        if self.data_all.iloc[-1, :].isna().values.all():
            self.data_all.drop(self.data_all.tail(1).index, inplace=True)

        ldpath = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 'input', 'labeldict.csv'
                )
            )

        result_labeling(self.data_all, labeldictpath=ldpath)
        self.data_all = self.data_all.loc[
            :, ~self.data_all.columns.duplicated()
            ].copy()

        self.data_caps = data_hnw_caps
        if self.tes_used:
            self.data_caps['cap_tes'] = data_tes_cap
        result_labeling(self.data_caps, labeldictpath=ldpath)

        for col in self.data_all.columns:
            if ('status' in col[-1]) or ('state' in col):
                self.data_all.drop(columns=col, inplace=True)

        self.data_caps = self.data_caps.to_frame().transpose()
        self.data_caps.reset_index(inplace=True, drop=True)
        for col in self.data_caps.columns:
            if ('total' in str(col)) or ('0' in str(col)):
                self.data_caps.drop(columns=col, inplace=True)

        try:
            self.data_all = self.data_all.reindex(
                sorted(self.data_all.columns), axis=1
                )
        except TypeError as e:
            print(f'TypeError in sorting data_all: {e}')

        try:
            self.data_caps = self.data_caps.reindex(
                sorted(self.data_caps.columns), axis=1
                )
        except TypeError as e:
            print(f'TypeError in sorting data_caps: {e}')

        # Prepare economic and ecologic data containers
        self.cost_df = pd.DataFrame()
        self.key_params = {}

    def calc_econ_params(self):
        for unit in self.param_units.keys():
            unit_E_N = self.data_caps.loc[0, f'cap_{unit}']
            add_cost = 0

            if unit == 'plb':
                add_cost = self.param_opt['energy_tax']
                E_N_label = f'Q_{unit}'
            elif unit == 'eb':
                E_N_label = f'Q_{unit}'
            elif unit == 'hp':
                E_N_label = f'Q_out_{unit}'
            elif unit == 'tes':
                E_N_label = f'Q_in_{unit}'
            elif unit in ['ccet', 'ice']:
                E_N_label = f'P_{unit}'
                unit_E_N = (
                    unit_E_N / self.param_units[unit]['eta_th']
                    * self.param_units[unit]['eta_el']
                    )
            self.cost_df = calc_cost(
                unit, unit_E_N, self.param_units, self.data_all[E_N_label],
                self.cost_df, add_var_cost=add_cost
                )

        # %% Primary energy and total cost calculation
        # total unit costs
        self.key_params['op_cost_total'] = self.cost_df.loc['op_cost'].sum()
        self.key_params['invest_total'] = self.cost_df.loc['invest'].sum()

        # total gas costs
        if 'H_source' in self.data_all.columns:
            self.key_params['cost_gas'] = (
                self.data_all['H_source'] * (
                    self.data['gas_price']
                    + self.data['co2_price'] * self.param_opt['ef_gas']
                    )
                ).sum()
        else:
            self.key_params['cost_gas'] = 0

        # total electricity costs
        if 'P_source' in self.data_all.columns:
            self.key_params['cost_el_grid'] = (
                self.data_all['P_source'] * (
                    self.data['el_spot_price']
                    + self.param_opt['elec_consumer_charges_grid']
                    )
                ).sum()
        else:
            self.key_params['cost_el_grid'] = 0


        if 'P_internal' in self.data_all.columns:
            self.key_params['cost_el_internal'] = (
                self.data_all['P_internal']
                * self.param_opt['elec_consumer_charges_self']
                ).sum()
        else:
            self.key_params['cost_el_internal'] = 0

        self.key_params['cost_el'] = (
            self.key_params['cost_el_grid']
            + self.key_params['cost_el_internal']
            )

        self.key_params['cost_total'] = (
            self.key_params['op_cost_total'] + self.key_params['cost_gas']
            + self.key_params['cost_el']
            )

        # %% Revenue calculation
        if 'P_internal' in self.data_all.columns:
            self.key_params['revenues_spotmarket'] = (
                self.data_all['P_spotmarket'] * (
                    self.data['el_spot_price'] + self.param_opt['vNNE']
                    )
                ).sum()
        else:
            self.key_params['revenues_spotmarket'] = 0

        self.key_params['revenues_heat'] = (
            self.data_all['Q_demand'].sum() * self.param_opt['heat_price']
            )

        self.key_params['revenues_total'] = (
            self.key_params['revenues_spotmarket']
            + self.key_params['revenues_heat']
            )

        # %% Total balance
        self.key_params['balance_total'] = (
            self.key_params['revenues_total'] - self.key_params['cost_total']
            )

        # %% Meta results
        # self.key_params['objective'] = self.meta_results['objective']
        # self.key_params['gap'] = (
        #     (self.meta_results['problem']['Lower bound']
        #     - self.meta_results['objective'])
        #     / self.meta_results['problem']['Lower bound'] * 100
        #     )

        # %% Main economic results
        self.key_params['LCOH'] = LCOH(
            self.key_params['invest_total'], self.key_params['cost_total'],
            self.data_all['Q_demand'].sum(),
            revenue=(
                self.key_params['revenues_total']
                - self.key_params['revenues_heat']
                ),
            i=self.param_opt['capital_interest'], n=self.param_opt['lifetime']
            )

        self.key_params['total_heat_demand'] = self.data_all['Q_demand'].sum()

    def calc_ecol_params(self):
        self.data_all['Emissions OM'] = 0

        if 'H_source' in self.data_all.columns:
            self.data_all['Emissions OM'] += (
                self.data_all['H_source'] * self.param_opt['ef_gas']
                )
            self.key_params['Emissions OM (Gas)'] = (
                self.data_all['H_source'] * self.param_opt['ef_gas']
                ).sum()
        else:
            self.key_params['Emissions OM (Gas)'] = 0

        if 'P_source' in self.data_all.columns:
            self.data_all['Emissions OM'] += (
                self.data_all['P_source'] * self.data['ef_om']
                )
            self.key_params['Emissions OM (Electricity)'] = (
                self.data_all['P_source'] * self.data['ef_om']
                ).sum()
        else:
            self.key_params['Emissions OM (Electricity)'] = 0

        if 'P_spotmarket' in self.data_all.columns:
            self.data_all['Emissions OM'] -= (
                self.data_all['P_spotmarket'] * self.data['ef_om']
                )
            self.key_params['Emissions OM (Spotmarket)'] = (
                self.data_all['P_spotmarket'] * self.data['ef_om'] * -1
                ).sum()
        else:
            self.key_params['Emissions OM (Spotmarket)'] = 0

        self.key_params['Total Emissions OM'] = (
            self.data_all['Emissions OM'].sum()
            )

    def run_model(self):
        self.generate_buses()
        self.generate_sources()
        self.generate_sinks()
        self.generate_components()
        self.solve_model()

    def run_postprocessing(self):
        self.get_results()
        self.calc_econ_params()
        self.calc_ecol_params()

def calc_bwsf(i, n):
    """Berechne Barwert Summenfaktor.
    
    Parameters:
    -----------
    i : float
        Kapitalzins als rationale Zahl (nicht Prozent)

    n : int
        Lebensdauer des Investments in Jahren
    """
    q = 1+i
    return (q**n - 1)/(q**n * (q - 1))

def LCOH(invest, cost, Q, revenue=0, i=0.05, n=20):
    """Konstantin 2013, Markus [29].

    LCOH        Wärmegestehungskosten
    invest:     Investitionsausgaben zum Zeitpunkt t=0
    bwsf:       Barwert Summenfaktor
    cashflow:   Differenz aller Einnahmen und Ausgaben (Zahlungsströme)
                innerhalb des betrachteten Jahres
    Q:          Gesamte bereitgestellte Wärmemenge pro Jahr
    i:          Kalkulationszinssatz
    n:          Betrachtungsdauer
    """
    q = 1 + i
    bwsf = (q**n - 1)/(q**n * (q - 1))

    LCOH = (invest + bwsf * (cost - revenue))/(bwsf * Q)
    return LCOH

def calc_cost(label, E_N, param, uc, cost_df, add_var_cost=None):
    """
    Calculate invest and operational cost for a unit.

    Parameters
    ----------

    label : str
        Label of unit to be used as column name in cost DataFrame.

    E_N : float
        Nominal rated energy that the specific cost relate to.

    param : dict
        JSON parameter file of user defined constants.

    uc : pandas.DataFrame
        DataFrame containing the units results of the unit commitment
        optimization.

    cost_df : pandas.DataFrame
        DataFrame in which the calculated cost should be inserted.
    """
    cost_df.loc['invest', label] =  param[label]['inv_spez'] * E_N
    cost_df.loc['op_cost_fix', label] = param[label]['op_cost_fix'] * E_N
    cost_df.loc['op_cost_var', label] = (
        param[label]['op_cost_var'] * uc.sum()
        )
    if add_var_cost:
        cost_df.loc['op_cost_var', label] += add_var_cost * uc.sum()
    cost_df.loc['op_cost', label] = (
        cost_df.loc['op_cost_fix', label] + cost_df.loc['op_cost_var', label]
        )

    return cost_df

def result_labeling(df, labeldictpath='labeldict.csv'):
    """
    Relabel the column names of oemof.solve result dataframes.

    Parameters
    ----------

    df : pandas.DataFrame
        DataFrame containing the results whose column names should be relabeled.
    
    labeldictpath : str
        Relative path to the labeldict csv file. Defaults to a path in the same
        directory.
    """
    labeldict_csv = pd.read_csv(labeldictpath, sep=';', na_filter=False)

    labeldict = dict()
    for idx in labeldict_csv.index:
        labeldict[
            ((labeldict_csv.loc[idx, 'name_out'],
              labeldict_csv.loc[idx, 'name_in']),
              labeldict_csv.loc[idx, 'type'])
            ] = labeldict_csv.loc[idx, 'label']

    if isinstance(df, pd.DataFrame):
        for col in df.columns:
            if col in labeldict.keys():
                df.rename(columns={col: labeldict[col]}, inplace=True)
            else:
                print(f'Column name "{col}" not in "{labeldictpath}".')
    elif isinstance(df, pd.Series):
        for idx in df.index:
            if idx in labeldict.keys():
                df.rename(index={idx: labeldict[idx]}, inplace=True)
            else:
                print(f'Column name "{idx}" not in "{labeldictpath}".')
