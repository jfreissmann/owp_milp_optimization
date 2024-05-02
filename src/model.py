import oemof.solph as solph
import pandas as pd


class EnergySystem():
    """Model class that builds the energy system from parameters."""

    def __init__(self, data, param_units, param_opt):
        self.data = data
        self.param_units = param_units
        self.param_opt = param_opt

        self.periods = len(data.index)
        self.es = solph.EnergySystem(
            timeindex=pd.date_range(
                data.index[0], periods=self.periods, freq='h'
                ),
            infer_last_interval=False
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
                            max=self.param_units['Q_rel_max'],
                            min=self.param_units['Q_rel_min'],
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

            if unit in ['hp', 'plb']:
                if unit == 'hp':
                    eff = 'cop'
                    input_nw = 'enw'
                    var_cost = self.param_units[unit]['op_cost_var']
                elif unit == 'plb':
                    eff = 'eta'
                    input_nw = 'gnw'
                    var_cost = (
                        self.param_units[unit]['op_cost_var']
                        + self.param_opt['energy_tax']
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
                            max=self.param_units['Q_rel_max'],
                            min=self.param_units['Q_rel_min'],
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
                    balanced=self.param_units['balanced']
                    )

                self.es.add(self.comps[unit])

        if internal_el:
            self.comps['chp_internal'] = solph.components.Converter(
                label='chp_internal',
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
        self.model.solve(
            solver='gurobi', solve_kwargs={'tee': True},
            cmdline_options={'MIPGap': self.param_opt['MIPGap']}
            )

    def run_model(self):
        self.generate_buses()
        self.generate_sources()
        self.generate_sinks()
        self.generate_components()
        self.solve_model()


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
