import pyppfd.solar as light
import structure.model as structure
import towers.model as tower
import fryield.model as plants
import robot.model as rbt
import hvac.model as hvac
import nutrients.digestor as nutrients
import pandas as pd

cases = []
report = None

default_params = {'light':{'angle_max':90,'cloud_cover':0.25},
          'climate':{'amb_day_C':32,'amb_night_C':27,
                     'amb_day_RH':70,'amb_night_RH':85,
                     'rainfall_mm_wk':40},
          'prices':{'electricity_kwh':0.18},
          'structure':{'num_floors':1,'height_m':2.8,'building_L':150,'building_W':15},
          'tower':{'plant_spacing_cm':62,'plant_clearance_cm':35},
          'plants':{'leaf_ccr':0.6,'fr_harvest_weeks':40,'rep_growth':0.35},
          'robot':{},
          'hvac':{},
          'nutrients':{},
          'config':{'period':'A'},
          'capex':{'total':750000,'structure':0,'tower':0,
                   'robot':0,'hvac':100000,'nutrient':100000},
          'opex':{'total':12000,'structure':0,'tower':0,
                   'robot':0,'hvac':1000,'nutrient':1000},
          'kpi':{'facade_wall_area':825,'fruit_kg_yr':11400,
                 'revenue':46000,'profit':20000,'return':0.0325,
                 'ps_rate_molCO2_m2_d':8,
                 'num_towers':183,'num_plants':2196,
                 'rep_tsp_L_d':878,'rep_tsp_mL_pl_d':400,
                 'yield_kg_m2_yr':13.9,'total_n_g_d':62}
          }

case_params = {}

def run_cases(cases):
    global report
    for c in cases:
        for x in c:
            if not c[x] == {}:
                for k in c[x]:
                    case_params[x][k] = c[x][k]
        update()
        c.update(case_params)
    report = pd.DataFrame.from_records(cases)

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
    global case_params
    case_params['light'] = light.update(case_params['light'])
    case_params['structure'] = structure.update(case_params['structure'])
    case_params['tower'] = tower_update(case_params)
    case_params['plants'] = plants_update(case_params)
    case_params['robot'] = robot_update(case_params)
    case_params['hvac'] = hvac.update(case_params['hvac'])
    case_params['nutrients'] = nutrients.update(case_params['nutrients'])
    kpi_update(case_params)

def tower_update(params):
    structure_keys = ['height_m','facade_L','width_m']
    tower_params = params['tower'].copy()
    for k in structure_keys:
        tower_params[k] = params['structure'][k]
    tower_params = tower.update(tower_params)
    return tower_params


def plants_update(params):
    pass

def robot_update(params):
    pass

def kpi_update(params):
    pass


