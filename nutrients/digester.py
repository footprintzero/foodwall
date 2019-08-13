import pandas as pd
import numpy as np
from food import nutrition as nut
from design import equipment as eqp
from utils import chemistry as chem
import math

SUBGROUPS = ['prices','revenue','opex','capex','energy']
CONSTANTS = {'density_air_kg_m3':1.255,
             'O2_in_air':0.21,

    }

default_params = {'supply_N_gpd':1084,
                  'feed_N_gpd':2168,
                  'feed_load_kgph':17.25,
                  'feed_wet_pct':0.60,
                  'feed_browns_pct':0.37,
                  'feed_bones_pct':0.3,
                  'feed_water_pct':0.69,
                  'feed_dry_C':0.468,
                  'feed_dry_H':0.0672,
                  'feed_dry_O':0.4472,
                  'feed_dry_N':0.0169,
                  'feed_dry_S':0.0011,
                  'feed_CN':27.7,
                  'digestate_CN':12.0,
                  'feed_HHV_kJ_kg':17575,
                  'biogas_HHV_kJ_kg':16037,
                  'digestate_HHV_kJ_kg':11305,
                  'ACE_HHV_kJ_kg':4916,
                  'biogas_yield_kJ_g':9.88,
                  'biogas_rate_dry_kgph':123.5,
                  'flue_rate_wet_kgph':1403.0,
                  'air_wet_kgph':1380.0,
                  'air_abs_hum':0.017,
                  'flue_abs_hum':0.022,
                  'N_recovery':0.5,
                  'AN_N_immob':0.37,
                  'AE_energy_yield':0.9,
                  'AN_capacity_factor_kgpd_m3':10.0,
                  'AN_tank_size_ratio':4.0,
                  'AE_capacity_factor_kgpd_m3':50.0,
                  'feed_turnover_days':14,
                  'nutrient_turnover_days':0.5,
                  'recycle_ratio':2.0,
                  'nutrient_ratio':20.0,
                  'O2_g_kJ':0.142,
                  'AN1_mixing_factor_kW_m3':0.1,
                  'AN2_mixing_factor_kW_m3':0.05,
                  'AN3_mixing_factor_kW_m3':0.05,
                  'AE1_mixing_factor_kW_m3':0.1,
                  'feed_mixing_factor_kW_m3':0.05,
                  'nutrient_mixing_factor_kW_m3':0.05,
                  'blending_power_LOW_kJ_kg':7.5,
                  'blending_power_HIGH_kJ_kg':30.0,
                  'additives_conc_ppmwt':100,
                  'NH3_oxidation_kJ_mol':284,
                  'ARU_simple_return':0.03,
                  'prices':{'tank_wall_matl_USD_m2':45.0,'dist_piping':0.3,
                            'dist_EI_auto':0.18,'auto_intensity_USD_kW':8000.0,
                            'ARU_cost_factor':0.8,'sterilizer_USD_20kgpd':1000.0,
                            'cons_labor_factor':1.5,'additives_USD_kg':40,'dosing_USD_m3':50.0,
                            'electricity_kwh':0.18,'burner_cost_factor_USD_kW':50.0,
                            'thermal_energy_discount':0.90},
                  'revenue':{'total_USD':20,'biogas':2850},
                  'capex':{'total_USD':206000.0,'tanks':2850,'vessels':23000,'mixers':12500.0,
                           'ARU':11000.0,'burner':1000.0,'pre_treaters':1800,'dosing':2000,'sterilizer':1000.0,
                           'pumps':300,'blowers':600.0,'piping':16700.0,'EI_auto':10000,'cons_labor':124000.0},
                  'opex':{'total_USD':8000.0,'mixers':5000.0,'pre_treaters':60.0,'dosing':300.0,
                           'pumps':300,'blowers':100.0,'EI_auto':2000.0},
                  'energy':{'total_kW':8000.0,'mixers':5000.0,'pre_treaters':60.0,'dosing':300.0,
                           'pumps':300,'blowers':100.0,'EI_auto':2000.0},
                  }

case_params = {}

def setup():
    global case_params, default_parameters
    case_params = default_params.copy()


def update(params=None):
    global SUBGROUPS
    setup()
    if params is not None:
        for p in params:
            if p in SUBGROUPS:
                for s in params[p]:
                    case_params[p][s] = params[p][s]
            else:
                case_params[p] = params[p]
    run()
    return case_params.copy()

def run():
    quick_pfd()
    #process_simulation()
    size_equipment()
    cost_estimation()
    set_energy()
    set_kpi()

"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    quick_pfd
"""

def quick_pfd():
    set_feedrate_kgph()
    set_process_rates_kgph()
    set_biogas_yield_MJ_d()
    set_airflow_kgph()

def set_feedrate_kgph():
    case = case_params.copy()

    supply_N_gpd = case['supply_N_gpd']; N_recovery = case['N_recovery']
    feed_CN  = case['feed_CN'] ;  feed_dry_C = case['feed_dry_C']
    feed_water_pct = case['feed_water_pct']

    feed_N_gpd = supply_N_gpd/N_recovery

    wet_load_gpd = wet_load_from_total_N(feed_N_gpd,
                                           CN=feed_CN,
                                           dry_C=feed_dry_C,water_pct=feed_water_pct)

    feed_load_kgph = wet_load_gpd*1/(24*1000)

    case_params['feed_N_gpd'] = feed_N_gpd
    case_params['feed_load_kgph'] = feed_load_kgph

def wet_load_from_total_N(total_N_gpd,CN=27.7,dry_C=0.468,water_pct=0.69):
    dry_kg = total_N_gpd*CN/dry_C
    wet_kg = dry_kg / (1-water_pct)
    return wet_kg

def set_process_rates_kgph():
    case = case_params.copy()
    feed_load_kgph = case['feed_load_kgph']
    AN1_load_kgph = feed_load_kgph*case['recycle_ratio']
    AE1_load_kgph = feed_load_kgph
    nutrient_load_kgph = feed_load_kgph*case['nutrient_ratio']*case['N_recovery']

    case_params['AN1_load_kgph']= AN1_load_kgph
    case_params['AE1_load_kgph']= AE1_load_kgph
    case_params['nutrient_load_kgph']= nutrient_load_kgph


def set_biogas_yield_MJ_d():
    global case_params
    case = case_params.copy()
    air_kg_m3 = CONSTANTS['density_air_kg_m3']
    biogas_rate_MJ_d = case['feed_load_kgph']*case['biogas_yield_kJ_g']*24
    case_params['biogas_rate_MJ_d'] = biogas_rate_MJ_d
    case_params['biogas_rate_dry_kgph'] = biogas_rate_MJ_d/case['biogas_HHV_kJ_kg']*1000/24
    case_params['biogas_rate_dry_m3ph'] = case_params['biogas_rate_dry_kgph']/air_kg_m3


def set_airflow_kgph():
    global case_params
    case = case_params.copy()
    biogas_dry_kgph = case['biogas_rate_dry_kgph']
    biogas_dry_MJph = case['biogas_rate_MJ_d']/24
    O2_g_kJ = case['O2_g_kJ']
    O2_in_air = CONSTANTS['O2_in_air']
    air_dry_kgph = O2_g_kJ*biogas_dry_MJph*1/(1-O2_in_air)
    flue_dry_kgph = air_dry_kgph + biogas_dry_kgph

    case['air_wet_kgph']=air_dry_kgph*1/(1-case['air_abs_hum'])
    case['flue_rate_wet_kgph']=flue_dry_kgph*1/(1-case['flue_abs_hum'])

"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    size equipment
"""

equipment = {'tanks':{},
             'vessels':{},
            'mixers':{},
            'pre_treaters':{},
            'burner':{},
            'dosing':{},
            'pumps':{},
            'blowers':{},
            'ARU':{},
            'sterilizer':{},
            'piping':{},
            'EI_auto':{},
            }


EQP_SPECS = {'tanks':{'feed':{
                            'eqp_type':'tank',
                            'loading_kgph':17.25,
                            'turnover_days':14,
                            'mixer':True,
                            'pump':True,
                            'blower':False,
                            },
                     'nutrient':{
                            'eqp_type':'tank',
                            'loading_kgph':10*17.25,
                            'turnover_days': 0.5,
                            'mixer':True,
                            'pump':True,
                            'blower':False,
                            }
                     },
            'vessels':{
                    'AN1': {
                        'eqp_type': 'tank',
                        'loading_kgph': 2*17.25,
                        'turnover_days': 8.3,
                        'mixer': True,
                        'pump': False,
                        'blower': False,
                    },
                    'AN2': {
                        'eqp_type': 'tank',
                        'loading_kgph': 2 * 17.25,
                        'turnover_days': 8.3,
                        'mixer': True,
                        'pump': False,
                        'blower': False,
                    },
                    'AN3': {
                        'eqp_type': 'tank',
                        'loading_kgph': 2 * 17.25,
                        'turnover_days': 33.3,
                        'mixer': True,
                        'pump': True,
                        'blower': False,
                    },
                    'AE1': {
                        'eqp_type': 'tank',
                        'loading_kgph': 17.25,
                        'turnover_days': 20,
                        'mixer': True,
                        'pump': False,
                        'blower': False,
                    },
            },
            'mixers': {
                'AN1': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'LP_mixing',
                    'loading_kgph': 2*17.25,
                    'LP_mixing_factor_kW_m3': 0.1,
                },
                'AN2': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'LP_mixing',
                    'loading_kgph': 2*17.25,
                    'LP_mixing_factor_kW_m3': 0.05,
                },
                'AN3': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'LP_mixing',
                    'loading_kgph': 2*17.25,
                    'LP_mixing_factor_kW_m3': 0.05,
                },
                'AE1': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'LP_mixing',
                    'loading_kgph': 17.25,
                    'LP_mixing_factor_kW_m3': 0.1,
                },
                'feed': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'LP_mixing',
                    'loading_kgph': 17.25,
                    'LP_mixing_factor_kW_m3': 0.05,
                },
                'nutrient': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'LP_mixing',
                    'loading_kgph': 10*17.25,
                    'LP_mixing_factor_kW_m3': 0.05,
                },
            },
            'pre_treaters': {
                'PT_wet': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'HP_blending',
                    'loading_kgph': 0.6 * 17.25,
                    'HP_blending_factor_kJ_kg': 0.25*30,
                    'HP_blending_hpd': 0.5,
                },
                'PT_browns': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'HP_blending',
                    'loading_kgph': 0.37 * 17.25,
                    'HP_blending_factor_kJ_kg': 0.25*30,
                    'HP_blending_hpd': 0.5,
                },
                'PT_bones': {
                    'eqp_type': 'mixer',
                    'sizing_model': 'HP_blending',
                    'loading_kgph': 0.3 * 17.25,
                    'HP_blending_factor_kJ_kg': 30,
                    'HP_blending_hpd': 0.5,
                },
            },
            'pumps':{
                    'feed': {
                        'eqp_type': 'pump',
                        'loading_kgph': 17.25,
                        'head_kPa': 400,
                        'operation_hpd': 12.0,
                    },
                    'AN3': {
                        'eqp_type': 'pump',
                        'loading_kgph': 2*17.25,
                        'head_kPa': 300,
                        'operation_hpd': 24.0,
                    },
                    'nutrient': {
                        'eqp_type': 'pump',
                        'loading_kgph': 10*17.25,
                        'head_kPa': 75,
                        'operation_hpd': 24.0,
                    },
                    },
            'blowers':{
                    'flue_gas': {
                        'eqp_type': 'blower',
                        'loading_kgph': 2*17.25,
                        'head_kPa': 20,
                        'operation_hpd': 24.0,
                    },
                    },
            'burner':{
                    'offgas': {
                        'eqp_type': 'furnace',
                        'duty_kW': 23,
                            }
                    },
            'ARU':{
                    'ARU': {
                        'eqp_type': 'ARU',
                        'loading_kgph': 2*17.25,
                            }
                    },
            'sterilizer':{
                    'sterilizer': {
                        'eqp_type': 'sterilizer',
                        'loading_kgph': 2*17.25,
                                }
                    },
            'dosing':{
                    'dosing': {
                        'eqp_type': 'dosing',
                        'loading_kgph': 2*17.25,
                            }
                    },
            }


def size_equipment():
    update_equipment_specs()
    size_tanks()
    size_vessels()
    size_mixers()
    size_pre_treaters()
    size_burner()
    size_pumps()
    size_blowers()
    size_ARU()
    size_sterilizer()
    size_dosing()

def update_equipment_specs():
    #tanks, vessels
    case = case_params.copy()

    feed_load_kgph = case['feed_load_kgph']
    EQP_SPECS['tanks']['feed']['loading_kgph'] = case['feed_load_kgph']
    EQP_SPECS['tanks']['nutrient']['loading_kgph'] = case['nutrient_load_kgph']

    EQP_SPECS['vessels']['AN1']['loading_kgph'] = case['AN1_load_kgph']
    EQP_SPECS['vessels']['AN2']['loading_kgph'] = case['AN1_load_kgph']
    EQP_SPECS['vessels']['AN3']['loading_kgph'] = case['AN1_load_kgph']
    EQP_SPECS['vessels']['AE1']['loading_kgph'] = case['AE1_load_kgph']

    EQP_SPECS['tanks']['feed']['turnover_days'] = case['feed_turnover_days']
    EQP_SPECS['tanks']['nutrient']['turnover_days'] = case['nutrient_turnover_days']

    AN_turnover_days = 1000/case['AN_capacity_factor_kgpd_m3']*1/case['recycle_ratio']
    AN_ratio = case['AN_tank_size_ratio']
    EQP_SPECS['vessels']['AN1']['turnover_days'] =AN_turnover_days/(2+AN_ratio)
    EQP_SPECS['vessels']['AN2']['turnover_days'] =AN_turnover_days/(2+AN_ratio)
    EQP_SPECS['vessels']['AN3']['turnover_days'] =AN_turnover_days*AN_ratio/(2+AN_ratio)
    EQP_SPECS['vessels']['AE1']['turnover_days'] =1000/case['AE_capacity_factor_kgpd_m3']

    for grp in ['tanks','vessels']:
        for eqp in EQP_SPECS[grp]:
            EQP_SPECS[grp][eqp]['tank_wall_matl_USD_m2']= case['prices']['tank_wall_matl_USD_m2']

    #mixers
    EQP_SPECS['mixers']['feed']['LP_mixing_factor_kW_m3'] = case['feed_mixing_factor_kW_m3']
    EQP_SPECS['mixers']['nutrient']['LP_mixing_factor_kW_m3'] = case['feed_mixing_factor_kW_m3']
    EQP_SPECS['mixers']['AN1']['LP_mixing_factor_kW_m3'] = case['AN1_mixing_factor_kW_m3']
    EQP_SPECS['mixers']['AN2']['LP_mixing_factor_kW_m3'] = case['AN2_mixing_factor_kW_m3']
    EQP_SPECS['mixers']['AN3']['LP_mixing_factor_kW_m3'] = case['AN3_mixing_factor_kW_m3']
    EQP_SPECS['mixers']['AE1']['LP_mixing_factor_kW_m3'] = case['AE1_mixing_factor_kW_m3']

    #pre-treaters
    EQP_SPECS['pre_treaters']['PT_wet']['loading_kgph'] = case['feed_wet_pct']*feed_load_kgph
    EQP_SPECS['pre_treaters']['PT_browns']['loading_kgph'] = case['feed_browns_pct']*feed_load_kgph
    EQP_SPECS['pre_treaters']['PT_bones']['loading_kgph'] = case['feed_bones_pct']*feed_load_kgph

    EQP_SPECS['pre_treaters']['PT_wet']['HP_blending_factor_kJ_kg'] = case['blending_power_LOW_kJ_kg']
    EQP_SPECS['pre_treaters']['PT_browns']['HP_blending_factor_kJ_kg'] = case['blending_power_LOW_kJ_kg']
    EQP_SPECS['pre_treaters']['PT_bones']['HP_blending_factor_kJ_kg'] = case['blending_power_HIGH_kJ_kg']

    #pumps


    #blowers
    EQP_SPECS['blowers']['flue_gas']['loading_kgph'] = case['flue_rate_wet_kgph']


    #burner
    EQP_SPECS['burner']['offgas']['duty_MJ_d'] = case['flue_rate_wet_kgph']
    EQP_SPECS['burner']['offgas']['burner_cost_factor_USD_kW'] = case['prices']['burner_cost_factor_USD_kW']


    #sterilizer
    for eqp in EQP_SPECS['sterilizer']:
        EQP_SPECS['sterilizer'][eqp]['loading_kgph'] = case['AE1_load_kgph']
        EQP_SPECS['sterilizer'][eqp]['sterilizer_USD_20kgpd']= case['prices']['sterilizer_USD_20kgpd']


    #dosing
    for eqp in EQP_SPECS['dosing']:
        EQP_SPECS['dosing'][eqp]['loading_kgph'] = feed_load_kgph
        EQP_SPECS['dosing'][eqp]['additives_USD_kg']= case['prices']['additives_USD_kg']
        EQP_SPECS['dosing'][eqp]['additives_conc_ppmwt']= case['additives_conc_ppmwt']
        EQP_SPECS['dosing'][eqp]['dosing_USD_m3']= case['prices']['dosing_USD_m3']


    #ARU
    for eqp in EQP_SPECS['ARU']:
        EQP_SPECS['ARU'][eqp]['supply_N_gpd']= case['supply_N_gpd']
        EQP_SPECS['ARU'][eqp]['AN_N_immob']= case['AN_N_immob']
        EQP_SPECS['ARU'][eqp]['ARU_cost_factor']= case['prices']['ARU_cost_factor']
        EQP_SPECS['ARU'][eqp]['simple_return']= case['ARU_simple_return']
        EQP_SPECS['ARU'][eqp]['NH3_oxidation_kJ_mol']= case['NH3_oxidation_kJ_mol']

    #electricity price
    for grp in EQP_SPECS:
        for eqp in EQP_SPECS[grp]:
            EQP_SPECS[grp][eqp]['electricity_kwh']= case['prices']['electricity_kwh']

def size_tanks():
    global equipment
    eqp_group = 'tanks'
    eqp_type = 'tank'
    specs = EQP_SPECS[eqp_group].copy()
    for tk_key in specs:
        load_rate_kgph = specs[tk_key]['loading_kgph'] ; turnover_days = specs[tk_key]['turnover_days']
        if specs[tk_key]['eqp_type']==eqp_type:
            tk = eqp.TankEqp(load_rate_kgph,**specs[tk_key])
        equipment[eqp_group][tk_key] =tk
        EQP_SPECS[eqp_group][tk_key]['V_m3'] = tk.V_m3
        EQP_SPECS[eqp_group][tk_key]['capex'] = tk.capex
        EQP_SPECS[eqp_group][tk_key]['opex'] = tk.opex
        if specs[tk_key]['mixer']:
            EQP_SPECS['mixers'][tk_key]['loading_kgph'] = tk.load_rate_kgph
            EQP_SPECS['mixers'][tk_key]['V_m3']  = tk.V_m3
        if specs[tk_key]['pump']:
            EQP_SPECS['pumps'][tk_key]['loading_kgph'] = tk.load_rate_kgph


def size_vessels():
    eqp_group = 'vessels'
    eqp_type = 'tank'
    global equipment
    specs = EQP_SPECS[eqp_group].copy()
    for vs_key in specs:
        load_rate_kgph = specs[vs_key]['loading_kgph'] ; turnover_days = specs[vs_key]['turnover_days']
        if specs[vs_key]['eqp_type'] == eqp_type:
            vs = eqp.TankEqp(load_rate_kgph,**specs[vs_key])
        equipment[eqp_group][vs_key] = vs
        EQP_SPECS[eqp_group][vs_key]['V_m3'] = vs.V_m3
        EQP_SPECS[eqp_group][vs_key]['capex'] = vs.capex
        EQP_SPECS[eqp_group][vs_key]['opex'] = vs.opex
        if specs[vs_key]['mixer']:
            EQP_SPECS['mixers'][vs_key]['loading_kgph'] = vs.load_rate_kgph
            EQP_SPECS['mixers'][vs_key]['V_m3'] = vs.V_m3
            EQP_SPECS['mixers'][vs_key]['capex'] = vs.capex
        if specs[vs_key]['pump']:
            EQP_SPECS['pumps'][vs_key]['loading_kgph'] = vs.load_rate_kgph


def size_mixers():
    global equipment
    USD_kWh = case_params['prices']['electricity_kwh']
    eqp_group = 'mixers'
    eqp_type = 'mixer'
    specs = EQP_SPECS[eqp_group].copy()
    for mx_key in specs:
        loading_kgph = specs[mx_key]['loading_kgph']
        if specs[mx_key]['eqp_type'] == eqp_type:
            vs = eqp.MixerEqp(loading_kgph,**specs[mx_key])
        equipment[eqp_group][mx_key] = vs
        EQP_SPECS[eqp_group][mx_key]['energy_kW'] = vs.energy_kW
        EQP_SPECS[eqp_group][mx_key]['capex'] = vs.capex
        EQP_SPECS[eqp_group][mx_key]['opex'] = vs.opex


def size_pre_treaters():
    global equipment
    eqp_group = 'pre_treaters'
    eqp_type = 'mixer'
    specs = EQP_SPECS[eqp_group].copy()
    for mx_key in specs:
        loading_kgph = specs[mx_key]['loading_kgph']
        if specs[mx_key]['eqp_type'] == eqp_type:
            vs = eqp.MixerEqp(loading_kgph,**specs[mx_key])
        equipment[eqp_group][mx_key] = vs
        EQP_SPECS[eqp_group][mx_key]['energy_kW'] = vs.energy_kW
        EQP_SPECS[eqp_group][mx_key]['capex'] = vs.capex
        EQP_SPECS[eqp_group][mx_key]['opex'] = vs.opex


def size_pumps():
    global equipment
    eqp_group = 'pumps'
    eqp_type = 'pump'
    specs = EQP_SPECS[eqp_group].copy()
    for key in specs:
        loading_kgph = specs[key]['loading_kgph']
        head_kPa = specs[key]['head_kPa']
        del specs[key]['head_kPa']
        if specs[key]['eqp_type'] == eqp_type:
            eq = eqp.PumpEqp(loading_kgph,head_kPa,**specs[key])
        equipment[eqp_group][key] = eq
        EQP_SPECS[eqp_group][key]['head_kPa'] = head_kPa
        EQP_SPECS[eqp_group][key]['energy_kW'] = eq.energy_kW
        EQP_SPECS[eqp_group][key]['energy_MAX_kW'] = eq.energy_MAX_kW
        EQP_SPECS[eqp_group][key]['capex'] = eq.capex
        EQP_SPECS[eqp_group][key]['opex'] = eq.opex


def size_blowers():
    global equipment
    eqp_group = 'blowers'
    eqp_type = 'blower'
    specs = EQP_SPECS[eqp_group].copy()
    for key in specs:
        loading_kgph = specs[key]['loading_kgph']
        head_kPa = specs[key]['head_kPa']
        del specs[key]['head_kPa']
        if specs[key]['eqp_type'] == eqp_type:
            eq = eqp.PumpEqp(loading_kgph,head_kPa,**specs[key])
        equipment[eqp_group][key] = eq
        EQP_SPECS[eqp_group][key]['head_kPa'] = head_kPa
        EQP_SPECS[eqp_group][key]['energy_kW'] = eq.energy_kW
        EQP_SPECS[eqp_group][key]['energy_MAX_kW'] = eq.energy_MAX_kW
        EQP_SPECS[eqp_group][key]['capex'] = eq.capex
        EQP_SPECS[eqp_group][key]['opex'] = eq.opex


def size_burner():
    global equipment
    eqp_group = 'burner'
    eqp_type = 'burner'
    specs = EQP_SPECS[eqp_group].copy()
    for key in specs:
        duty_MJ_d = specs[key]['duty_MJ_d']
        cost_factor_USD_kW = specs[key]['burner_cost_factor_USD_kW']
        energy_kW = duty_MJ_d/(24*3.6)
        capex = energy_kW*cost_factor_USD_kW
        EQP_SPECS[eqp_group][key]['energy_kW'] = energy_kW
        EQP_SPECS[eqp_group][key]['capex'] = capex
        EQP_SPECS[eqp_group][key]['opex'] = 0


def size_ARU():
    specs = EQP_SPECS['ARU']['ARU'].copy()
    MW_NH3 = chem.mol_W('N1H3')
    specs['loading_kgph'] = specs['supply_N_gpd']*1/24*1/1000*(1-specs['AN_N_immob'])
    enth_kWh_yr = specs['NH3_oxidation_kJ_mol']/MW_NH3*specs['loading_kgph']*24*365/3.6
    ann_eq_cost = enth_kWh_yr*specs['ARU_cost_factor']*specs['electricity_kwh']
    specs['energy_kW'] = 0
    specs['opex'] = 0
    specs['capex'] = ann_eq_cost/specs['simple_return']
    EQP_SPECS['ARU']['ARU'] = specs

def size_sterilizer():
    specs = EQP_SPECS['sterilizer']['sterilizer'].copy()
    num_units = math.ceil(specs['loading_kgph']/20)
    specs['capex'] = specs['sterilizer_USD_20kgpd']*num_units
    specs['opex'] = 0
    specs['energy_kW'] = 0
    EQP_SPECS['sterilizer']['sterilizer'] = specs


def size_dosing():
    specs = EQP_SPECS['dosing']['dosing'].copy()
    V_m3 = EQP_SPECS['tanks']['feed']['V_m3']
    specs['V_m3'] = V_m3
    specs['capex'] = specs['dosing_USD_m3']*V_m3
    additives_rate = specs['loading_kgph']*specs['additives_conc_ppmwt']*10**-6*24*365
    specs['opex'] = additives_rate*specs['additives_USD_kg']
    specs['energy_kW'] = 0
    EQP_SPECS['dosing']['dosing'] = specs

"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    cost estimation
"""

def cost_estimation():
    global case_params
    case = case_params.copy()
    capex_subtotal = get_equipment_costs('capex')
    opex_subtotal = get_equipment_costs('opex')
    capex = case_params['capex'].copy()
    opex = case_params['opex'].copy()
    capex['equipment'] = capex_subtotal
    opex['equipment'] = opex_subtotal
    capex = add_construction_costs(capex)
    capex['total_USD'] =  capex['total_capex']
    opex['total_USD'] =  opex['equipment']
    del capex['total_capex'],opex['equipment']
    case_params['capex']  = capex
    case_params['opex'] = opex
    set_biogas_value()

def set_biogas_value():
    global case_params
    case = case_params.copy()
    discount = case['prices']['thermal_energy_discount']
    revenue = case['biogas_rate_MJ_d']*365/3.6*case['prices']['electricity_kwh']*(1-discount)
    case_params['revenue']['biogas'] = revenue
    case_params['revenue']['total_USD'] = revenue


def get_equipment_costs(cost_group='capex'):
    case = case_params.copy()
    total_costs_USD = 0
    for grp in EQP_SPECS:
        eqp_group_cost = 0
        for eqp in EQP_SPECS[grp]:
            if cost_group in EQP_SPECS[grp][eqp]:
                eqp_group_cost+=EQP_SPECS[grp][eqp][cost_group]
        case_params[cost_group][grp] = eqp_group_cost
        total_costs_USD +=eqp_group_cost
    return total_costs_USD


def add_construction_costs(capex):
    global case_param
    case = case_params.copy()
    eqp_capex =capex['equipment']
    capex['piping'] = eqp_capex*case['prices']['dist_piping']
    capex['EI_auto']= eqp_capex*case['prices']['dist_EI_auto']
    materials = eqp_capex+capex['piping']+capex['EI_auto']
    capex['materials'] = materials
    cons_labor_factor = case['prices']['cons_labor_factor']
    cons_labor = construction_labor(materials,labor_factor=cons_labor_factor)
    capex['cons_labor'] = cons_labor
    capex['total_capex'] = materials+cons_labor
    return capex


def construction_labor(materials,labor_factor=1.5):
    return materials*labor_factor


def set_energy():
    global case_params
    case = case_params.copy()
    energy = case['energy']
    energy['EI_auto'] = case['capex']['EI_auto']/case['prices']['auto_intensity_USD_kW']
    USD_kWh = case['prices']['electricity_kwh']
    case_params['opex']['EI_auto'] = eqp.electricity_cost_USD_yr(energy['EI_auto'],USD_kWh)
    total_kW = sum([energy[x] for x in energy if not x=='total_kW'])
    energy['total_kW'] = total_kW
    case_params['energy'] = energy

def set_kpi():
    global case_params
    case = case_params.copy()
    supply_N_kg_yr = case['supply_N_gpd']*365/1000
    revenue = case['revenue']['total_USD']
    opex = case['opex']['total_USD']
    net_cost = opex-revenue
    capex = case['capex']['total_USD']
    ARU_simple_return = case['ARU_simple_return']
    case_params['N_cost_USD_kg'] = total_lifetime_cost(capex,net_cost,ARU_simple_return)/supply_N_kg_yr
    case_params['simple_return'] = -1*net_cost/capex


def total_lifetime_cost(capex,opex,cost_capital):
    return opex + capex*cost_capital

"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    process simulation
"""

feed = None
biogas = {}
digestate = {}
parameters = {}

streams = {'feed':{},
           'biogas':{},
           'digestate':{},
           'ACE':{},
           'fertilizer':{},
           'feed_air':{},
           'aerobic_offgas':{},
           'flue_gas':{},
           'sludge_recycle':{},
           'sludge_purge':{},
           }

class Stream(object):
    def __init__(self,diet):
        comp_dry = diet.elements()/diet.wt_g('dry')
        self.CHONS = [comp_dry[x] for x in ['C','H','O','N','S']]
        self.water_pct = diet.elements()/diet.wt_g('wet')
        self.kg_wet = diet.wt_g('wet')/1000
        self.kg_dry = diet.wt_g('dry')/1000
    def stoichiometric_biogas_yields_kg(self):
        x = self.CHONS
        MW = [12.0,1.01,16.0,14.0,32.0]
        yields = stoichiometric_biogas_yield_kg(
            x[0]/MW[0],x[1]/MW[1],x[2]/MW[2],x[3]/MW[3],x[4]/MW[4])
        yields_kg = [yields[c]*self.kg_dry for c in yields]
        return yields_kg

def set_feed(diet='sgp',d=None):
    global feed
    if diet == 'sgp':
        d = nut.sgp_diet()
    feed = nut.get_waste(d)

def stoichiometric_biogas_yield_kg(C,H,O,N,S):
    yields = {'CH4':0,'CO2':0,
              'NH3':0,'H2S':0}
    MW = [12.0+16.0*2,14.0+1.01*3,1.01*2+32.0,1.01*4+12]
    yields['CO2'] = C*MW[0] ; yields['NH3'] = N*MW[1]
    yields['H2S'] = S*MW[2]
    yields['CH4'] = (C+0.25*H-0.5*O-0.75*N-0.5*S)*MW[3]
    return yields

def process_simulation():
    pass