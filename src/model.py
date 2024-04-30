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

        self.buses = {}
        self.comps = {}

    def generate_buses(self):
        self.buses['gnw'] = solph.Bus(label='gas network')
        self.buses['enw'] = solph.Bus(label='electricity network')
        self.buses['hnw'] = solph.Bus(label='heat network')
        self.buses['spotmarket_node'] = solph.Bus(label='spotmarket node')

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

    def run_model(self):
        self.generate_buses()
        self.generate_sources()
