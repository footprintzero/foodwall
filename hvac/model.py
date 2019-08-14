import pandas as pd
import math as m
import psypy.psySI as si
from utils.num_methods import newton
import numpy as np

SUBGROUPS = ['prices','energy','capex','opex']


# hello world
hvac_parameters = {
                   'bio_kw':66.218,
                   'num_vents': 24,
                   'num_circ_fans': 13,
                   'num_il_fans': 24,
                   'cop_refr': 3.5,
                   'cop_dess': 1,
                   't_rate': .006,  # transpiration rate in L/min/plant
                   'insolence': .25047,  # light in kw/m2
                   'rf': .1,  # reflection factor constant
                   'u': 3,  # heat transfer constant for pmma
                   'roof_a': 504,
                   'wall_a': 957.6,
                   'num_towers': 185,
                   'p_tower': 12,
                   'daytime': True,
                   'i_temp_d': 300.15,
                   'i_humidity_d': .65,
                   'i_temp_n': 298.15,
                   'i_humidity_n': .75,
                   'a_temp_d': 305.15,
                   'a_humidity_d': .70,
                   'a_temp_n': 300.15,
                   'a_humidity_n': .85,
                   'day_hours': 12,
                   'weeks_on': 40,
                   'il_fan_speed': 10,
                   'il_kw': .2,
                   'shape': 'square',
                   'duct_kg': 13876,
                   'building_l': 150,
                   'building_w': 15,
                   'systemw': 1.5,
                   'systemh': 2.8,
                   'circulation_min': 1,
                   'circ_fan_cfm': 4000,
                   'circ_kw': .2,
                   'il_space': 30,
                   'f_hvac_cfm': 40000,
                   'f_nv_cfm':0,
                   'supply_temperature':0,
                   'supply_humidity':0,
                   'day_btu':396711.65,
                   'night_btu':40241.44,
                   'floors':1,
                   'true_for_dess':True,
                   'prices': {'electricity_kwh': .18, 'c_gas_p': 8.04972, 'i_gas_p': 4.16472,
                              'steel_price': .6, 'circ_fan_price': 125, 'il_fan_price': 150,
                              'vent_price': 20, 'main_unit_price': .075, 'dess_factor': 20,
                              'installation_factor': 1.25, 'ic_factor': .5},
                   'energy': {'circ_kw': 3.9,'il_kw': 9.6,'main_unit_kw': 116.3,
                              't_kw': 50.2, 'u_kw': 29.5, 'l_kw': 36.6},
                   'capex': {'total_usd_refr': 54730,'total_usd_dess': 761373,'ducts': 8326,
                             'vents': 480,'il_fans': 3600,'circ_fans': 1625,
                             'main_unit_refr': 29753,'main_unit_dess': 595067},
                   'opex': {'total_usd_refr': 33808,'il_fans': 3790,'circ_fans': 4838,
                            'total_usd_dess': 9559, 'main_unit_dess': 929,'main_unit_refr': 25179},
                   }


working_params = {}


def setup():
    global working_params
    global hvac_parameters
    working_params = hvac_parameters.copy()


def run():
    global working_params
    prices = working_params['prices']
    energy = working_params['energy']
    capex = working_params['capex']
    opex = working_params['opex']
    if working_params['supply_humidity']>0 and working_params['supply_temperature']==0:
        x = working_params['supply_humidity']
        kwargs = {'supply_humidity':x}
    elif working_params['supply_temperature']>0 and working_params['supply_humidity']==0:
        y = working_params['supply_temperature']
        kwargs = {'supply_temperature':y}
    elif working_params['supply_humidity']>0 and working_params['supply_temperature']>0:
        x= working_params['supply_humidity']
        y = working_params['supply_temperature']
        kwargs = {'supply_humidity':x,'supply_temperature':y}
    else:
        kwargs = {}

    itd = working_params['i_temp_d']
    ihd = working_params['i_humidity_d']
    atd = working_params['a_temp_d']
    ahd = working_params['a_humidity_d']

    itn = working_params['i_temp_n']
    ihn = working_params['i_humidity_n']
    atn = working_params['a_temp_n']
    ahn = working_params['a_humidity_n']
    [st,sh,fh,fn,mb,t,l,u]=get_supply(working_params['f_hvac_cfm'],working_params['t_rate'],
                                      working_params['insolence'],working_params['rf'],
                                      itd,ihd,atd,ahd,working_params['f_nv_cfm'],working_params['num_towers'],
                                      working_params['p_tower'],working_params['wall_a'],
                                      working_params['roof_a'],working_params['u'],True,**kwargs)

    working_params['day_btu']= mb
    energy['t_kw']=t
    energy['l_kw']=l
    energy['u_kw']=u
    energy['main_unit_kw']=t+l+u
    mbn = get_supply(working_params['f_hvac_cfm'], working_params['t_rate'],
                     working_params['insolence'], working_params['rf'],
                     itn, ihn, atn, ahn, working_params['f_nv_cfm'],
                     working_params['num_towers'],
                     working_params['p_tower'], working_params['wall_a'],
                     working_params['roof_a'], working_params['u'], False, **kwargs)[4]


    working_params['night_btu']=mbn
    working_params['f_hvac_cfm']=fh
    [dk,ck,ik,nf,ni,nv] = duct_fans_info(working_params['f_hvac_cfm'],working_params['il_fan_speed'],
                                         working_params['il_kw'],working_params['shape'],
                                         working_params['building_l'],working_params['building_w'],
                                         working_params['systemw'],working_params['systemh'],
                                         working_params['circulation_min'],working_params['circ_fan_cfm'],
                                         working_params['circ_kw'],working_params['il_space'])
    working_params['duct_kg']=dk
    energy['circ_kw']=ck
    energy['il_kw']=ik
    working_params['num_circ_fans']=nf
    working_params['num_il_fans']=ni
    working_params['num_vents']=nv
    [cc,vc,ifc,cfc,dc,mc] = cap_cost(working_params['day_btu'],prices['dess_factor'],
                                     working_params['duct_kg'],working_params['num_circ_fans'],
                                     working_params['num_il_fans'],working_params['num_vents'],
                                     prices['steel_price'],prices['circ_fan_price'],
                                     prices['il_fan_price'],prices['vent_price'],prices['main_unit_price'],
                                     prices['installation_factor'],working_params['floors'])
    capex['total_usd_dess']=cc
    capex['vents']=vc
    capex['il_fans']=ifc
    capex['circ_fans']=cfc
    capex['ducts']=dc
    capex['main_unit_dess']=mc
    v=prices['dess_factor']
    capex['main_unit_refr']=(mc/v)
    capex['total_usd_refr']= prices['installation_factor']*((mc/v)+dc+cfc+ifc+vc)
    [tfo,cfo,ifo]=fans_op_cost(ck,ik,working_params['weeks_on'],working_params['day_hours'],
                               prices['electricity_kwh'],mb,mbn,working_params['floors'])
    opex['circ_fans']=ifo
    opex['il_fans']=cfo
    desso = dess_op_cost(prices['c_gas_p'],prices['i_gas_p'],prices['ic_factor'],
                         working_params['day_hours'],working_params['weeks_on'],
                         working_params['bio_kw'],working_params['cop_dess'],mb,mbn,working_params['floors'])

    if desso<0:
        desso=0
    opex['main_unit_dess'] = desso
    opex['total_usd_dess']=desso+tfo
    refro = refr_op_cost(prices['electricity_kwh'],working_params['day_hours'],working_params['weeks_on'],
                         working_params['cop_refr'],mb,mbn,working_params['floors'])
    opex['main_unit_refr']=refro
    opex['total_usd_refr']=refro+tfo


def run_cases(cases):
    global report
    for c in cases:
        for k in c:
            working_params[k] = c[k]
        update()
        c.update(working_params)
    report = pd.DataFrame.from_records(cases)
    return report


def update(params=None):
    global SUBGROUPS
    setup()
    if params is not None:
        for p in params:
            if p in SUBGROUPS:
                for s in params[p]:
                    working_params[p][s] = params[p][s]
            else:
                working_params[p] = params[p]
    run()
    return working_params.copy()


def get_supply(f_hvac_cfm=40000,t_rate=.006, insolence=.25047, rf=.1, i_temp=300.15, i_humidity=.65,
               a_temp=305.15, a_humidity=.7,f_nv_cfm=0, num_towers=185,
               p_tower=12, wall_a=957.6, roof_a=504, u=3, daytime=True, **kwargs):
    air_density = 1.2   # kg/m3
    f_nv = f_nv_cfm*(1/60)*.0283168*air_density
    if 'supply_humidity' in kwargs:
        supply_humidity = kwargs['supply_humidity']
        f_hvac_cfm = newton(hvac_wrapper_humidity,supply_humidity,20000,hfull=1,dh=500,ymax=None)[0]
    if 'supply_temperature' in kwargs:
        supply_temperature = kwargs['supply_temperature']
        f_hvac_cfm = newton(hvac_wrapper_temp,supply_temperature,20000,hfull=.25,dh=500,ymax=None)[0]
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
        return [supply_temperature,supply_humidity,fhvac_incfm,f_nv_cfm,maxbtu,t_kw,l_kw,u_kw]

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
    try:
        hum = np.nan
        supply = si.state("H", h_supply,"W", ah_supply,101325)
        if supply[2]>=1:
            raise ValueError('humidity greater than 1 %s' % hum)
    except:
        raise ValueError('humidity greater than 1 %s or something with AH %s enthalpy %s combo' % (hum, ah_supply, h_supply))
    (supply_temp, supply_humidity) = (supply[0], supply[2])
    max_btu_required = (t_kw+l_kw+u_kw)*3412.142
    return [supply_temp, supply_humidity, f_hvac_cfm,f_nv_cfm, max_btu_required,t_kw,l_kw,u_kw]


def hvac_wrapper_humidity(F):
    results = get_supply(f_hvac_cfm=F)
    humidity = results[1]
    return humidity


def hvac_wrapper_temp(F):
    results = get_supply(f_hvac_cfm=F)
    temp = results[0]
    return temp


def duct_fans_info(f_hvac_cfm=40000,il_fan_speed=10,il_kw=.2,shape='square',
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
    ikw=il_kw*(f_hvac_cfm/45000)
    il_fan_kw = num_il_fans*ikw
    duct_kg = duct_m2*6.86*2  # 6.86kg/m2 is standard galvanized steel sheet weight
    system_volume = systemh*((building_l+(2*systemw))*(building_w+(2*systemw))-(building_l*building_w))
    system_cfm = system_volume*35.3147*circulation_min
    num_circ_fans = m.ceil(system_cfm/circ_fan_cfm)
    circ_fan_kw = num_circ_fans*circ_kw
    num_vents=num_il_fans
    return duct_kg, circ_fan_kw, il_fan_kw, num_circ_fans,num_il_fans,num_vents


def cap_cost(max_btu_required=396711.65, dess_factor=20, duct_kg=13876.84, num_circ_fans=13, num_il_fans=24,
             num_vents=24, steel_price=.6, circ_fan_price=125, il_fan_price=150, vent_price=20,
             main_unit_price=.075, installation_factor=1.25,floors=1):
    vent_cost = vent_price*num_vents*installation_factor*2
    il_fan_cost = il_fan_price*num_il_fans*installation_factor*2
    circ_fan_cost = circ_fan_price*num_circ_fans*installation_factor*2
    duct_cost = duct_kg*steel_price*installation_factor
    main_cost = main_unit_price*max_btu_required*dess_factor*(floors**.95)*installation_factor
    capital_cost = vent_cost+il_fan_cost+circ_fan_cost+duct_cost+main_cost
    return capital_cost,vent_cost,il_fan_cost,circ_fan_cost,duct_cost,main_cost


def refr_op_cost(kw_price=.18,day_hours=12,weeks_on=40,
                 cop_refr=3.5,day_btu=396711.65,night_btu=100603.59,floors=1):
    main_unit_day = (day_btu/cop_refr)*.000293*day_hours*7*weeks_on*kw_price
    main_unit_night = (night_btu/cop_refr)*.000293*(24-day_hours)*7*weeks_on*kw_price
    main_unit_total = (main_unit_day+main_unit_night)*floors
    return main_unit_total


def dess_op_cost(c_gas_p=8.04972,i_gas_p=4.16472,ic_factor=.5,day_hours=12,
                 weeks_on=40,bio_kw=66.218,cop_dess=1,day_btu=396711.65,night_btu=100603.59,floors=1):
    bio_btu=bio_kw/.000293
    real_bio_btu=cop_dess*bio_btu
    gas_price = (((c_gas_p-i_gas_p)*ic_factor)+i_gas_p)/1000000
    if bio_btu > night_btu:
        excess_btu = ((real_bio_btu-night_btu)*(24-day_hours))/day_hours
        final_btu = day_btu-bio_btu-excess_btu
        main_unit_day = (final_btu / cop_dess) * day_hours * 7 * weeks_on * gas_price
        main_unit_total = main_unit_day*floors
    else:
        main_unit_day = ((day_btu-bio_btu)/cop_dess)*day_hours*7*weeks_on*gas_price
        main_unit_night = ((night_btu-bio_btu)/cop_dess)*(24-day_hours)*7*weeks_on*gas_price
        main_unit_total = (main_unit_day+main_unit_night)*floors
    return main_unit_total


def fans_op_cost(circ_fan_kw=4,il_fan_kw=5,weeks_on=40,day_hours=12,
                 kw_price=.18,day_btu=396711.65,night_btu=40241.44,floors=1):
    circ_fans_total = circ_fan_kw*24*7*weeks_on*kw_price
    il_fans_day = il_fan_kw * day_hours * 7 * weeks_on * kw_price
    il_fans_night = il_fan_kw * (night_btu/day_btu) * (24 - day_hours) * 7 * weeks_on * kw_price
    il_fans_total = il_fans_day+il_fans_night
    fans_total = (il_fans_total + circ_fans_total)*floors
    return fans_total,il_fans_total,circ_fans_total
