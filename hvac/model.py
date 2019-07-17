import pandas as pd
import math as m
import psypy.psySI as si
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
                         't_rate': .0006, #transpiration rate in L/min/plant
                         'insolence': .25047, #light in kw/m2
                         'rf':.1, #reflection factor constant
                         'u':3, #heat transfer constant for pmma
                         'outside_btu': 118680,
                         'cfm': '.0333 cfm/btu',
                         's_temp_d': 'unknown',
                         's_humidity_d': 'unknown',
                         's_temp_n': 'unknown',
                         's_humidity_n': 'unknown',
                         'i_temp_d': 27,
                         'i_humidity_d': 75,
                         'i_temp_n': 25,
                         'i_humidity_n': 85,
                         'a_temp_d':32,
                         'a_humidity_d':70,
                         'a_temp_n': 32,
                         'a_humidity_n': 70,
                         'length_of_day':12,
                         'length_of_night':12
                         },
                   'capex':{},
                   'opex':{}
                   }


working_params = {}

def setup():
    global working_params, hvac_parameters
    working_params = hvac_parameters

def run():
    pass
    #tbd


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


def get_supply_return_btu(t_rate, insolence, rf, i_temp, i_humidity, a_temp, a_humidity,
                          f_hvac, f_nv, num_towers, p_tower, wall_a, roof_a, u, cop, daytime):
    h_hat2 = si.state("DBT", a_temp, "RH", a_humidity, 101325)[1]
    h_hat3 = si.state("DBT", i_temp, "RH", i_humidity, 101325)[1]
    ah2 = si.state("DBT", a_temp, "RH", a_humidity, 101325)[4]
    ah3 = si.state("DBT", i_temp, "RH", i_humidity, 101325)[4]
    if daytime:
        enthalpy_water = 2260
        t_kw = t_rate*(enthalpy_water/60)*num_towers*p_tower
        l_kw = insolence*(wall_a+roof_a)*rf
        u_kw = (u*(wall_a+(2*roof_a))*(a_temp-i_temp))/1000
        t_water = t_rate*(1/60)*num_towers*p_tower
    else:
        t_kw = 0
        l_kw = 0
        u_kw = (u*(wall_a+(2*roof_a))*(a_temp-i_temp))/1000
        t_water = 0
    h_return = h_hat3+(t_kw + l_kw + u_kw)/(f_hvac+f_nv)
    h_supply = ((h_hat3*(f_hvac+f_nv))-(f_nv*h_hat2))/f_hvac
    ah_return = ah3+(t_water/(f_nv+f_hvac))
    ah_supply = ((ah3*(f_hvac+f_nv))-(f_nv*ah2))/f_hvac

    supply = si.state("H", h_supply,"W", ah_supply,101325)
    (supply_temp, supply_humidity) = (supply[0], supply[2])
    sreturn = si.state("H", h_return,"W", ah_return,101325)
    (return_temp, return_humidity) = (sreturn[0], sreturn[2])
    max_btu_required = ((f_hvac*(h_return-h_supply))/cop)*3412.142
    return [supply_temp, supply_humidity, return_temp, return_humidity, max_btu_required]


def get_total_kwh():
    pass


def cap_cost():
    pass



def op_cost():
    pass
