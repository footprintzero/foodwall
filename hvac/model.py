import pandas as pd
import math as m
import psypy as psy

hvac_parameters = {'duct':
                        {'duct_length': 330,
                         'duct_csa': .5,
                         'num_vents': 45,
                         'duct_velocity': 'unknown',
                         'duct_cfm': 'unknown',
                         'duct_material': 'steel sheet'
                         },
                   'cfans':
                        {'num_cfans': 45,
                         'cfan_cfm': 1000,
                         'cfan_velocity': 1,
                         'kwh_per_day': .1,
                         'natural_ventilation_factor': .4,
                         'type': 'unknown'
                         },
                   'main_unit':
                        {'total_btu': 1500000,
                         'cop': 3.5,
                         'kwh_per_day': 1200,
                         'dess_factor': 'unknown',
                         'solar_factor': 'unknown',
                         'transpiration_btu': 1365000,
                         'sunlight_btu': 'unknown',
                         'outside_btu': 118680,
                         'cfm': '.0333 cfm/btu',
                         'supply_temp': 'unknown',
                         'supply_humidity': 'unknown',
                         'return_temp': 25,
                         'return_humidity': 60
                         },
                   'capex':{},
                   'opex':{}
                   }


working_params = {}

def setup():
    global working_params, hvac_parameters
    working_params = hvac_parameters

def run():
    tbd


def run_cases(cases):
    global report
    for c in cases:
        for x in c:
            if not c[x] == {}:
                for k in c[x]:
                    working_params[x][k] = c[x][k]
        update()
        c.update(working_params)
    report = pd.DataFrame.from_records(cases)




def update(params=None):
    setup()
    if params is not None:
        for p in params:
            working_params[p] = params[p]
    run()
    return working_params.copy()



def get_total_btu():
    #find transpiration btu from transpiration rate, find sunlight btu from sun model, find outside btu from ambient cond



def get_total_kwh():
    #sum all kwh from all systems of hvac and include additional factors


def get_psy():
    #psychrometric conditions


def cap_cost():
    #cap cost


def op_cost():
    #op cost