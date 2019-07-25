import pandas as pd
import numpy as np
from food import nutrition as nut
from design import equipment as eqp

CONSTANTS = {'density_air_kg_m3':1.255,

    }

default_params = {'supply_N_gpd':1084,
                  'feed_N_gpd':2168,
                  'feed_load_kgph':414,
                  'feed_water_pct':0.69,
                  'feed_dry_C':0.468,
                  'feed_dry_H':0.0672,
                  'feed_dry_O':0.4472,
                  'feed_dry_N':0.0169,
                  'feed_dry_S':0.0011,
                  'feed_CN':27.7,
                  'digestate_CN':12,
                  'feed_HHV_kJ_kg':17575,
                  'biogas_HHV_kJ_kg':16037,
                  'digestate_HHV_kJ_kg':11305,
                  'ACE_HHV_kJ_kg':4916,
                  'biogas_yield_kJ_g':9.88,
                  'N_recovery':0.5,
                  'AN_N_immob':0.37,
                  'AE_energy_yield':0.9,
                  'AN_capacity_factor_kgpd_m3':10,
                  'AE_capacity_factor_kgpd_m3':2,
                  'recycle_ratio':2,
                  'nutrient_ratio':20,
                  'O2_g_kJ':0.142,
                  'AN1_mixing_factor_kW_m3':0.1,
                  'AN2_mixing_factor_kW_m3':0.05,
                  'AN3_mixing_factor_kW_m3':0.05,
                  'AE1_mixing_factor_kW_m3':0.1,
                  'feed_mixing_factor_kW_m3':0.05,
                  'nutrient_mixing_factor_kW_m3':0.05,
                  'blending_power_kJ_kg':30,
                  'prices':{'tank_wall_matl_USD_m2':45,'dist_piping':0.3,
                            'dist_EI_auto':0.18,'auto_intensity_USD_kW':8000,
                            'ARU_cost_factor':0.8,'sterilizer_40m3':1000,
                            'cons_labor_factor':1.5,'dosing_USD_m3':50},
                  'capex':{'total_USD':206000,'tanks':2850,'vessels':23000,'mixers':12500,
                           'ARU':11000,'burner':1000,'pre_treaters':1800,'dosing':2000,'sterilizer':1000,
                           'pumps-blowers':600,'piping':16700,'EI_auto':10000,'const_labor':124000},
                  'opex':{'total_USD':8000,'mixers':5000,'pre_treaters':60,'dosing':300,
                           'pumps-blowers':400,'EI_auto':2000},
                  }

case_params = {}

def setup():
    global case_params, default_parameters
    case_params = default_params


def update(params=None):
    setup()
    global case_params
    if params is not None:
        for p in params:
            case_params[p] = params[p]
    run()
    return case_params.copy()

def run():
    quick_pfd()
    #process_simulation()
    size_equipment()

"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    quick_pfd
"""

def quick_pfd():
    set_feedrate_kgph()
    set_process_rates_kgph()
    set_turnover_days()
    set_mixer_specs()
    get_airflow_kgph()
    get_biogas_yield_MJ_d()

def set_feedrate_kgph():
    case = case_params.copy()
    #'supply_N_gpd': 1084,
    # 'feed_N_gpd': 2168,
    #'feed_load_kgph': 414,
    #'feed_water_pct': 0.69,
    # 'feed_dry_C': 0.468,
    # 'feed_dry_H': 0.0672,
    #'feed_dry_O': 0.4472,
    # 'feed_dry_N': 0.0169,
    # 'feed_dry_S': 0.0011,
    #'feed_CN': 27.7,
    #'digestate_CN': 12,
    #'feed_HHV_kJ_kg': 17575,
    #  'biogas_HHV_kJ_kg': 16037,
    #'digestate_HHV_kJ_kg': 11305,
    #'ACE_HHV_kJ_kg': 4916,
    # 'biogas_yield_kJ_g': 9.88,
    # 'N_recovery': 0.5,

    feed_load_kgph = 1
    case['feed_load_kgph'] = feed_load_kgph

def set_process_rates_kgph():
    case = case_params.copy()
    feed_load_kgph = case['feed_load_kgph']
    AN1_load_kgph = feed_load_kgph*case['recycle_ratio']
    AE1_load_kgph = feed_load_kgph
    nutrient_load_kgph = feed_load_kgph*['nutrient_ratio']*case['N_recovery']
    case['AN1_load_kgph']= AN1_load_kgph
    case['AE1_load_kgph']= AE1_load_kgph
    case['nutrient_load_kgph']= nutrient_load_kgph

def set_turnover_days():
    pass

def set_mixer_specs():
    pass

def get_biogas_yield_MJ_d():
    pass

def get_airflow_kgph():
    pass


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
            'ammonia':{},
            'sterilizer':{},
            'piping':{},
            'EI_automation':{},
            }

EQP_SPECS = {'tanks':{'feed':{
                            'eqp_type':'tank',
                            'loading_kgph':17.25,
                            'turnover_days':14,
                            'mixer':True,
                            },
                     'nutrient':{
                            'eqp_type':'tank',
                            'loading_kgph':10*17.25,
                            'turnover_days': 0.5,
                            'mixer':True,
                            }
                     },
            'vessels':{
                    'AN1': {
                        'eqp_type': 'tank',
                        'loading_kgph': 2*17.25,
                        'turnover_days': 8.3,
                        'mixer': True,
                    },
                    'AN2': {
                        'eqp_type': 'tank',
                        'loading_kgph': 2 * 17.25,
                        'turnover_days': 8.3,
                        'mixer': True,
                    },
                    'AN3': {
                        'eqp_type': 'tank',
                        'loading_kgph': 2 * 17.25,
                        'turnover_days': 33.3,
                        'mixer': True,
                    },
                    'AE1': {
                        'eqp_type': 'tank',
                        'loading_kgph': 17.25,
                        'turnover_days': 20,
                        'mixer': True,
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
                'PT_brown': {
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
            #'burner': [],
            #'dosing': [],
            #'pumps': [],
            #'blowers': [],
            #'ammonia': [],
            #'sterilizer': [],
            #'piping': [],
            #'EI_automation': [],
            }

def size_equipment():
    size_tanks()
    size_vessels()
    size_mixers()
    size_pretreaters()
    size_pumps()
    size_blowers()

def size_tanks():
    global equipment
    specs = EQP_SPECS['tanks'].copy()
    for tk_key in specs:
        load_rate_kgph = specs[tk_key]['loading_kgph'] ; turnover_days = specs[tk_key]['turnover_days']
        if specs[tk_key]['eqp_type']=='tank':
            tk = eqp.TankEqp(load_rate_kgph,turnover_days,specs[tk_key])
        equipment['tanks'][tk_key] =tk
        if specs[tk_key]['mixer']:
            EQP_SPECS['mixers'][tk_key]['loading_kgph'] = tk.load_rate_kgph
            EQP_SPECS['mixers'][tk_key]['V_m3']  = tk.V_m3

def size_vessels():
    global equipment
    specs = EQP_SPECS['vessels'].copy()
    for vs_key in specs:
        load_rate_kgph = specs[vs_key]['loading_kgph'] ; turnover_days = specs[vs_key]['turnover_days']
        if specs[vs_key]['eqp_type'] == 'tank':
            vs = eqp.TankEqp(load_rate_kgph, turnover_days, specs[vs_key])
    equipment['vessels'][vs_key] = vs
    if specs[vs_key]['mixer']:
        EQP_SPECS['mixers'][vs_key]['loading_kgph'] = vs.load_rate_kgph
        EQP_SPECS['mixers'][vs_key]['V_m3'] = vs.V_m3



def size_mixers():
    pass


def size_pretreaters():
    pass

def size_pumps():
    pass

def size_blowers():
    pass


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