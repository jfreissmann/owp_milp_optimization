# OWP Optimization Dashboard

Energy system optimization dashboard using mixed integer linear programming.
Developed as part of the project "Offene Wärmespeicherplanung (OWP)" as part of
*Inno!Nord* of the *T!Raum* initiative funded by the German Federal Ministry of Education and Research.

## Key Features

- Combined invest and dispatch optimization based on [oemof.solph](https://github.com/oemof/oemof-solph)
- Parametrization and result visualizaiton with a [Streamlit](https://github.com/streamlit/streamlit) dashboard
- Wide range of typical heating plants
- Comprehensive data base of heat load data, energy prices and emission factors

## Funding

[<img src="src\img\Logos_Förderer_ohnePTJ.png">](https://www.innovation-strukturwandel.de/strukturwandel/de/innovation-strukturwandel/t_raum/t_raum_node.html)

## Installation

For now, only direct download from the [GitHub Repository](https://github.com/jfreissmann/owp_milp_optimization) is supported, so just clone it locally or download a ZIP file of the code. If you are using [Miniforge](https://github.com/conda-forge/miniforge) or another environment management tool using [conda](https://docs.conda.io/en/latest/), you can create and activate a clean environment like this:

```
conda create -n my_new_env python=3.11
```

```
conda activate my_new_env
```

To use the optimization dashboard, the necessary dependencies have to be installed from the `requirements.txt` file. In a clean environment from the root directory the installation from this file could look like this:

```
python -m pip install -r requirements.txt
```

## Run the dashboard

Running the optimization dashboard is as easy as running the following command from the root directory in your virtual environment with dependencies installed:

```
streamlit run src\Home.py
```

## License

See the `LICENSE` file for further information.
