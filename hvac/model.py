import pandas as pd
import math as m
import psypy.psySI as si
from utils.num_methods import newton

SUBGROUPS = ['prices','energy','capex','opex']

# hello world
hvac_parameters = {
                   'booster fans': 20,
                   'num_vents': 50,
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
                   'il_fan_speed': 10,
                   'il_kw': .55,
                   'shape': 'square',
                   'building_l': 150,
                   'building_w': 15,
                   'systemw': 1.5,
                   'systemh': 2.8,
                   'circulation_min': 1,
                   'circ_fan_cfm': 4000,
                   'circ_kw': .3,
                   'il_space': 30,
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


def get_supply(t_rate=.0006, insolence=.25047, rf=.1, i_temp=300.15, i_humidity=.65,
               a_temp=305.15, a_humidity=.7,f_nv_cfm=0, num_towers=185,
               p_tower=12, wall_a=957.6, roof_a=504, u=3, daytime=True, **kwargs):
    air_density = 1.2   # kg/m3
    f_nv = f_nv_cfm*(1/60)*.0283168*air_density
    if'f_hvac_cfm' in kwargs:
        f_hvac_cfm = kwargs['f_hvac_cfm']
    if 'supply_humidity' in kwargs:
        supply_humidity = kwargs['supply_humidity']
        f_hvac_cfm = newton(hvac_wrapper_humidity,supply_humidity,15000,hfull=1,dh=500,ymax=None)[0]
    if 'supply_temperature' in kwargs:
        supply_temperature = kwargs['supply_temperature']
        f_hvac_cfm = newton(hvac_wrapper_temp,supply_temperature,15000,hfull=.25,dh=500,ymax=None)[0]
    if 'supply_humidity' in kwargs and 'supply_temperature' in kwargs:
        supply_temperature = kwargs['supply_temperature']
        supply_humidity = kwargs['supply_humidity']
        ambient_enth = si.state("DBT", a_temp, "RH", a_humidity, 101325)[1]
        ideal_enth = si.state("DBT", i_temp, "RH", i_humidity, 101325)[1]
        supply_enth = si.state("DBT",supply_temperature,"RH",supply_humidity,101325)[1]
        delta_enth1 = ideal_enth - supply_enth
        delta_enth2 = ideal_enth - ambient_enth
        if daytime:
            enthalpy_water = 2260
            t_kw = t_rate * (enthalpy_water / 60) * num_towers * p_tower
            l_kw = insolence * (wall_a + roof_a) * rf
            u_kw = (u * (wall_a + (2 * roof_a)) * (a_temp - i_temp)) / 1000
        else:
            t_kw = 0
            l_kw = 0
            u_kw = (u * (wall_a + (2 * roof_a)) * (a_temp - i_temp)) / 1000
        kw = t_kw+l_kw+u_kw
        fhvac = (kw-(f_nv*delta_enth2))/delta_enth1
        maxbtu = kw*3412.142
        fhvac_incfm = (fhvac*60)/(.0283168*air_density)
        return [supply_temperature,supply_humidity,fhvac_incfm,f_nv_cfm,maxbtu]

    f_hvac = f_hvac_cfm*(1/60)*.0283168*air_density  # convert to kg/s
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
    ah_3 = ah_4-(t_water/(f_nv+f_hvac))
    ah_supply = ((ah_3*(f_hvac+f_nv))-(f_nv*ah_2))/f_hvac
    supply = si.state("H", h_supply,"W", ah_supply,101325)
    (supply_temp, supply_humidity) = (supply[0], supply[2])
    max_btu_required = (t_kw+l_kw+u_kw)*3412.142
    return [supply_temp, supply_humidity, f_hvac_cfm, f_nv_cfm, max_btu_required]


def hvac_wrapper_humidity(F,params):
    results = get_supply(f_hvac_cfm=F)
    humidity = results[1]
    return humidity


def hvac_wrapper_temp(F,params):
    results = get_supply(f_hvac_cfm=F)
    temp = results[0]
    return temp


def duct_fans_info(f_hvac_cfm,il_fan_speed=10,il_kw=.55,shape='square',
                   building_l=150,building_w=15,systemw=1.5,systemh=2.8,
                   circulation_min=1,circ_fan_cfm=4000,circ_kw=.3,il_space=30):
    flow_metric = f_hvac_cfm*.000471947
    csa_ducts = flow_metric/il_fan_speed
    duct_m2 = 0
    if shape == 'circle':
        r = m.sqrt(csa_ducts/m.pi)
        c_ducts = 2*r*m.pi
        duct_m2 = c_ducts*2*(building_l + building_w+(2*systemw))
    elif shape == 'square':
        r = m.sqrt(csa_ducts)
        c_ducts = 4*r
        duct_m2 = c_ducts*2*(building_l + building_w+(2*systemw))
    num_il_fans = 2*m.ceil((2*(building_l + building_w+(2*systemw)))/il_space)
    il_fan_kw = num_il_fans*il_kw
    duct_kg = duct_m2*6.86*2  # 6.86kg/m2 is standard galvanized steel sheet weight
    system_volume = systemh*((building_l+(2*systemw))*(building_w+(2*systemw))-(building_l*building_w))
    system_cfm = system_volume*35.3147*circulation_min
    num_circ_fans = m.ceil(system_cfm/circ_fan_cfm)
    circ_fan_kw = num_circ_fans*circ_kw
    num_vents=num_il_fans
    return duct_kg, circ_fan_kw, il_fan_kw, num_circ_fans,num_il_fans,num_vents


def cap_cost(max_btu_required, cop, dessicant, duct_kg, num_circ_fans, num_il_fans,
             num_vents, steel_price, circ_fan_price, il_fan_price, vent_price,
             main_unit_price, installation_factor):
    vent_cost = vent_price*num_vents
    il_fan_cost = il_fan_price*num_il_fans
    circ_fan_cost = circ_fan_price*num_circ_fans
    duct_cost = duct_kg*steel_price
    main_cost = main_unit_price*(max_btu_required/cop)*dessicant
    capital_cost = (vent_cost+il_fan_cost+circ_fan_cost+duct_cost+main_cost)*installation_factor
    return capital_cost


def op_cost(kw_price,day_hours,refrigerant_amount,refrigerant_price,weeks_on,num_circ_fans,num_il_fans,
            circ_fans_kw,il_fans_kw,main_unit_kw):
    refrigerant_cost = refrigerant_price*refrigerant_amount
    circ_fans_total = num_circ_fans*circ_fans_kw*24*7*weeks_on*kw_price
    il_fans_total = num_il_fans*il_fans_kw*day_hours*7*weeks_on*kw_price
    main_unit_total = main_unit_kw*day_hours*7*weeks_on*kw_price
    operational_cost = refrigerant_cost+circ_fans_total+il_fans_total+main_unit_total
    return operational_cost
