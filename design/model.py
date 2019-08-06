import pyppfd.solar as light
import structure.model as structure
import towers.model as tower
import fryield.model as plants
import robot.model as rbt
import hvac.model as hvac
import nutrients.digester as digester
import design.climate as climate
import pandas as pd

cases = []
report = None
SUBGROUPS = ['climate','prices','structure','tower'
              'plants','robot','conveyor','hvac','nutrients',
              'maintenance','config','capex','opex','revenue','kpi']

default_params = {'climate':{'amb_day_C':32,'amb_night_C':27,'pro_day_C':30,'pro_day_RH':80,
                     'amb_day_RH':70,'amb_night_RH':85,'pro_night_C':27,'pro_night_RH':85,
                     'rainfall_mm_wk':40,'angle_max':90,'cloud_cover':0.25,'daylight_hrs':10,
                     '24hr_avg':{},'24hr_max':{},'day_avg':{},'night_avg':{}},
          'prices':{'electricity_kwh':0.18,'fruit_USD_kg':2.86},
          'structure':{'num_floors':1,'height_m':2.8,'building_L':150,'building_W':15},
          'tower':{'plant_spacing_cm':62,'plant_clearance_cm':35},
          'plants':{'harvest_extension':1,'rep_growth':0.25,'tsp_pct_leaf_energy':0.6,
                    'Ca_ubar':370,'leaf_light_capture':0.37,'LAI_pct':0.8,'leaf_allocation':0.35,
                    'tsp_mL_pl_d':220,'tsp_daymax_ml_pl_min':6.5,'ambient_climate':False},
          'robot':{'num_towers': 183,'trays_per_tower': 4,'fruit_pl_d_day': .56},
          'conveyor':{},
          'hvac':{},
          'nutrients':{'N_recovery':0.5,'supply_N_gpd':1084,
                       'biogas_yield_kJ_g':9.88,
                       'AN_capacity_factor_kgpd_m3':10,
                       'prices':{'thermal_energy_discount':0.9,
                                 },
                       },
          'maintenance':{},
          'config':{'period':'A'},
          'capex':{'total':750000,'structure':0,'tower':0,
                   'robot':0,'hvac':100000,'nutrient':100000},
          'opex':{'total':12000,'structure':0,'tower':0,
                   'robot':0,'hvac':1000,'nutrient':1000},
          'revenue':{'total':46000,'fruit':46000},
          'kpi':{'facade_wall_area':825,'fruit_kg_yr':11400,
                 'revenue':46000,'profit':20000,'simple_return':0.0325,
                 'ps_rate_molCO2_m2_d':8,
                 'num_towers':183,'num_plants':2196,
                 'rep_tsp_L_d':878,'rep_tsp_mL_pl_d':400,
                 'yield_kg_m2_yr':13.9,'total_n_g_d':62}
          }

case_params = {}


def setup():
    global case_params
    case_params = default_params.copy()


def update(params=None):
    setup()
    global case_params
    if not params is None:
        for p in params:
            if p in case_params:
                if isinstance(case_params[p],dict):
                    for s in params[p]:
                        case_params[p][s] = params[p][s]
                else:
                    case_params[p] = params[p]
            else:
                case_params[p] = params[p]
    run()
    return case_params.copy()

def run():
    global case_params
    case_params['climate'] = climate.update(case_params['climate'])
    case_params['structure'] = structure.update(case_params['structure'])
    case_params['tower'] = tower_update(case_params) #for structure
    case_params['plants'] = plants_update(case_params)
    case_params['tower'] = tower_update(case_params) #for irrigation
    case_params['robot'] = robot_update(case_params)
    #conveyor
    case_params['hvac'] = hvac.update(case_params['hvac'])
    nutrients_update(case_params)
    #maintenance
    financials_update(case_params)
    kpi_update(case_params)

def tower_update(params):
    tower_params = params['tower'].copy()
    structure_keys = ['height_m','facade_L','width_m']
    for k in structure_keys:
        tower_params[k] = params['structure'][k]
    tower_params['tsp_mL_pl_d'] = params['plants']['tsp_mL_pl_d']
    tower_params['prices'] = params['prices'].copy()
    tower_params = tower.update(tower_params)
    return tower_params

def plants_update(params):
    #net dli inside greenhouse
    plants_params = params['plants'].copy()
    plants_params['wall_transmissivity'] = params['structure']['wall_transmissivity']

    #climate
    plants_params['hourly'] = params['climate']['hourly'].copy()
    climate_keys = ['pro_day_C','pro_day_RH','pro_night_C','pro_night_RH']
    for k in climate_keys:
        plants_params[k] = params['climate'][k]

    #tower
    tower_keys = ['plant_spacing_cm','planting_density_pl_m2',
        'plant_hw','num_plants']
    for k in tower_keys:
        plants_params[k] = params['tower'][k]

    #others
    plants_params['tower_dia_cm'] = params['tower']['dia_cm']
    plants_params['prices'] = params['prices'].copy()

    plants_params = plants.update(plants_params)
    return plants_params

def robot_update(params):
    robot_params = params['robot'].copy()
    robot_params['num_towers'] = params['tower']['num_towers']
    robot_params['trays_per_tower'] = params['tower']['trays_per_tower']
    robot_params['fruit_pl_d_day'] = params['plants']['rep_fruit_pl_d_day']
    robot_params['prices'] = params['prices'].copy()
    robot_params = rbt.update(robot_params)
    return robot_params

def nutrients_update(case_params):
    case = case_params['nutrients'].copy()
    case['prices']['electricity_kwh'] = case_params['prices']['electricity_kwh']
    case['supply_N_gpd'] = case_params['plants']['total_n_g_d']
    case_params['nutrients'] = digester.update(case)


def financials_update(params):
    global case_params
    capex = case_params['capex'].copy()
    opex = case_params['opex'].copy()
    revenue = case_params['revenue'].copy()

    #capex
    capex['structure'] = params['structure']['capex']['structure_USD']
    capex['tower'] = params['tower']['capex']['towers_USD']
    capex['robot'] = params['robot']['capex']['total_USD']
    capex['nutrients'] = params['nutrients']['capex']['total_USD']
    #capex['conveyor']
    #capex['hvac']
    capex['total'] = sum([capex[x] for x in capex if not x == 'total'])

    #opex
    opex['tower'] = params['tower']['opex']['total']
    opex['robot'] = params['robot']['opex']['total_USD']
    opex['nutrients'] = params['nutrients']['opex']['total_USD']

    #opex['conveyor']
    #opex['hvac']
    #opex['maintenance']
    opex['total'] = sum([opex[x] for x in opex if not x == 'total'])

    #revenue
    revenue['fruit'] = params['plants']['revenue']['fruit_sale_USD_yr']
    revenue['biogas'] = params['nutrients']['revenue']['biogas']
    revenue['total'] = sum([revenue[x] for x in revenue if not x=='total'])

    case_params['capex'] = capex
    case_params['opex'] = opex
    case_params['revenue'] = revenue

def kpi_update(params):
    global case_params
    kpi = params['kpi'].copy()

    kpi['facade_wall_area'] = params['structure']['facade_wall_area']
    kpi['num_towers'] = params['tower']['num_towers']

    plant_kpis = ['fruit_kg_yr','yield_kg_m2_yr','ps_rate_molCO2_m2_d',
                  'total_n_g_d','rep_tsp_L_d','rep_tsp_mL_pl_d','num_plants']

    for pk in plant_kpis:
        kpi[pk] = params['plants'][pk]

    nutrients_kpis = ['N_recovery','N_cost_USD_kg']

    for pk in nutrients_kpis:
        kpi[pk] = params['nutrients'][pk]

    kpi['revenue'] = params['revenue']['total']
    kpi['opex'] = params['opex']['total']
    kpi['capex'] = params['capex']['total']

    kpi['capex_m2'] = kpi['capex']/kpi['facade_wall_area']
    kpi['capex_tower'] = kpi['capex']/kpi['num_towers']

    kpi['profit'] = kpi['revenue']-kpi['opex']
    if kpi['capex']>0:
        kpi['simple_return'] = kpi['profit']/kpi['capex']

    case_params['kpi'] = kpi