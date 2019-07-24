import pandas as pd
import math as m
import psypy.psySI as si

SUBGROUPS = ['prices','energy','capex','opex']

# hello world
hvac_parameters = {
                   'duct_length': 330,
                   'booster fans': 20,
                   'duct_csa': .5,
                   'num_vents': 50,
                   'duct_cfm': 'unknown',
                   'duct_material_cost': 25,  # cost of steel sheet duct / m2
                   'num_cfans': 45,
                   'cfan_cfm': 1000,
                   'kw_duct': .1,
                   'total_btu': 1500000,
                   'cop': 3.5,
                   'kwh_per_day': 1200,
                   'dess_factor': 'unknown',
                   't_rate': .0006,  # transpiration rate in L/min/plant
                   'insolence': .25047,  # light in kw/m2
                   'rf': .1,  # reflection factor constant
                   'u': 3,  # heat transfer constant for pmma
                   'roof_a':504,
                   'wall_a':957.6,
                   'num_towers': 184,
                   'p_tower':12,
                   'daytime':True,
                   'cfm': '.0333 cfm/btu',
                   's_temp_d': 'unknown',
                   's_humidity_d': 'unknown',
                   's_temp_n': 'unknown',
                   's_humidity_n': 'unknown',
                   'i_temp_d': 27,
                   'i_humidity_d': .65,
                   'i_temp_n': 25,
                   'i_humidity_n': .75,
                   'a_temp_d':32,
                   'a_humidity_d': .70,
                   'a_temp_n': 27,
                   'a_humidity_n': .85,
                   'day_hours': 12,
                   'weeks': 40,
                   'prices': {},
                   'energy': {},
                   'capex': {},
                   'opex': {}
                   }


working_params = {}


def setup():
    global working_params, hvac_parameters
    working_params = hvac_parameters


def run():
    pass


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


def get_supply(f_hvac_cfm,t_rate=.0006, insolence=.25047, rf=.1, i_temp=300.15, i_humidity=.65,
               a_temp=305.15, a_humidity=.7,f_nv_cfm=0, num_towers=185,
               p_tower=12, wall_a=957.6, roof_a=504, u=3, daytime=True):
    air_density = 1.2   # kg/m3
    f_hvac = f_hvac_cfm*(1/60)*.0283168*air_density  # convert to kg/s
    f_nv = f_nv_cfm*(1/60)*.0283168*air_density
    h_hat2 = si.state("DBT", a_temp, "RH", a_humidity, 101325)[1]
    h_hat4 = si.state("DBT", i_temp, "RH", i_humidity, 101325)[1]
    ah_2 = si.state("DBT", a_temp, "RH", a_humidity, 101325)[4]
    ah_4 = si.state("DBT", i_temp, "RH", i_humidity, 101325)[4]
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
    h_hat3 = h_hat4 - ((t_kw + l_kw + u_kw)/(f_hvac+f_nv))
    h_supply = ((h_hat3 * (f_hvac + f_nv)) - (f_nv*h_hat2)) / f_hvac
    ah_3 = ah_4-(t_water/(f_nv+f_hvac))  # problem probably here
    ah_supply = ((ah_3*(f_hvac+f_nv))-(f_nv*ah_2))/f_hvac
    supply = si.state("H", h_supply,"W", ah_supply,101325)
    (supply_temp, supply_humidity) = (supply[0], supply[2])
    max_btu_required = (f_hvac*(h_hat4-h_supply))*3412.142
    return [supply_temp, supply_humidity, f_hvac_cfm, f_nv_cfm, max_btu_required]

def hvac_wrapper_humidity(F,params):
    t_rate = params['t_rate']
    insolence = params['insolence']
    rf = params['rf']
    i_temp = params['i_temp']
    i_humidity = params['i_humidity']
    a_temp = params['a_temp']
    a_humidity = params['a_humidity']
    f_nv_cfm = params['f_nv_cfm']
    num_towers = params['num_towers']
    p_towers = params['p_towers']
    wall_a = params['wall_a']
    roof_a = params['roof_a']
    u = params['u']
    daytime = params['daytime']
    results = get_supply(t_rate,insolence,rf,i_temp,i_humidity,a_temp,a_humidity,F,f_nv_cfm,num_towers,p_towers,wall_a,roof_a,u,daytime)
    humidity = results[1]
    return humidity

def hvac_wrapper_temp(F,params):
    t_rate = params['t_rate']
    insolence = params['insolence']
    rf = params['rf']
    i_temp = params['i_temp']
    i_humidity = params['i_humidity']
    a_temp = params['a_temp']
    a_humidity = params['a_humidity']
    f_nv_cfm = params['f_nv_cfm']
    num_towers = params['num_towers']
    p_towers = params['p_towers']
    wall_a = params['wall_a']
    roof_a = params['roof_a']
    u = params['u']
    daytime = params['daytime']
    results = get_supply(t_rate,insolence,rf,i_temp,i_humidity,a_temp,a_humidity,F,f_nv_cfm,num_towers,p_towers,wall_a,roof_a,u,daytime)
    temp = results[0]
    return temp
  
def duct_fans_info(f_hvac_cfm,fan_speed=10,shape='square',building_lm=151.5,building_wm=16.5):
    flow_metric = f_hvac_cfm*.000471947
    csa_ducts = flow_metric/fan_speed
    duct_m2 = 0
    if shape == 'circle':
        r = m.sqrt(csa_ducts/m.pi)
        c_ducts = 2*r*m.pi
        duct_m2 = c_ducts*2*(building_lm + building_wm)
    elif shape == 'square':
        r = m.sqrt(csa_ducts)
        c_ducts = 4*r
        duct_m2 = c_ducts*2*(building_lm + building_wm)
    fan_kw = 0
    num_vents = 4
    num_il_fans = 3
    duct_kg = duct_m2*6.86*2  # 6.86kg/m2 is standard galvanized steel sheet weight
    return duct_kg, fan_kw, num_vents, num_il_fans

def get_total_kwh(weeks,cop,max_btu_required,day_hours):
    pass


def num_fans():
    pass


def cap_cost():
    pass


def op_cost():

    pass
