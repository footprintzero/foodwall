import pyppfd.solar as light
import structure.model as structure
import towers.model as tower
import fryield.model as plants
import robot.model as rbt
import hvac.model as hvac
import conveyor.model as conveyor
import nutrients.digester as digester
import design.climate as climate
import pandas as pd
import math

cases = []
report = None
SUBGROUPS = ['climate','prices','structure','tower'
              'plants','robot','conveyor','hvac','nutrients','nursery',
              'maintenance','config','capex','opex','revenue','kpi']

default_params = {'climate':{'amb_day_C':32,'amb_night_C':27,'pro_day_C':30,'pro_day_RH':80,
                     'amb_day_RH':70,'amb_night_RH':85,'pro_night_C':27,'pro_night_RH':85,
                     'rainfall_mm_wk':40,'angle_max':90,'cloud_cover':0.25,'daylight_hrs':10,
                     '24hr_avg':{},'24hr_max':{},'day_avg':{},'night_avg':{}},
          'prices':{'electricity_kwh':0.18,'fruit_USD_kg':2.86,
                    'labor_unsk_USD_hr':7.14,'labor_skill_premium':4.9},
          'structure':{'num_floors':1,'height_m':2.8,'building_L':150,'building_W':15},
          'tower':{'plant_spacing_cm':62,'plant_clearance_cm':35},
          'plants':{'harvest_extension':1,'rep_growth':0.25,'tsp_pct_leaf_energy':0.6,
                    'Ca_ubar':370,'leaf_light_capture':0.37,'LAI_pct':0.8,'leaf_allocation':0.35,
                    'tsp_mL_pl_d':220,'tsp_daymax_ml_pl_min':6.5,'ambient_climate':True},
          'robot':{'num_towers': 186,'trays_per_tower': 4,'fruit_pl_d_day': .56,'prices':{}},
          'conveyor':{'num_towers':186,'rpd':20,'weeks_on':40,'prices':{}},
          'hvac':{'f_hvac_cfm':40000,'bio_kw':66.218,'t_rate':.00296,'num_towers':186,'weeks_on':40,
                  'nv_dess_refr':'nv','prices':{}},
          'nutrients':{'N_recovery':0.5,'supply_N_gpd':1084,
                       'biogas_yield_kJ_g':9.88,
                       'AN_capacity_factor_kgpd_m3':10,
                       'prices':{'thermal_energy_discount':0.9,
                                 },
                       },
          'nursery':{'seed_per_tray':70,'trays_per_rack':16,'seed_survival_pct':0.67,
                     'LED_W_per_tray':80,
                     'prices':{'seed_cost_USD':0.005,
                               'rack_cost_USD':5000}
                     },
          'maintenance':{'hours_per_tower':2,'digester_hrs_1000m2':160,
                         'hvac_hrs_1000m2':120,'robot_hrs_1000m2':120,
                         'engineer_hrs_1000m2':30},
          'config':{'period':'A'},
          'capex':{'total':750000,'structure':0,'tower':0,'conveyor':100000,
                   'robot':0,'hvac':100000,'nutrients':100000},
          'opex':{'total':12000,'structure':0,'tower':0,'conveyor':3000,
                   'robot':0,'hvac':1000,'nutrients':1000},
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
    case_params['conveyor']= conveyor_update(case_params)

    nutrients_update(case_params)
    case_params['hvac'] = hvac_update(case_params)
    case_params['maintenance'] = maintenance_update(case_params)
    case_params['nursery'] = nursery_update(case_params)
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
    robot_params['prices'].update(params['prices'])
    robot_params['num_towers'] = params['tower']['num_towers']
    robot_params['trays_per_tower'] = params['tower']['trays_per_tower']
    robot_params['fruit_pl_d_day'] = params['plants']['rep_fruit_pl_d_day']
    robot_params = rbt.update(robot_params)
    return robot_params


def hvac_update(params):
    hvac_params = params['hvac'].copy()
    hvac_params['prices'].update(params['prices'])
    floors=params['structure']['num_floors']
    hvac_params['floors']=floors
    hvac_params['num_towers'] = (params['tower']['num_towers'])/floors
    hvac_params['p_tower'] = 3*params['tower']['trays_per_tower']
    bio_mj_day = params['nutrients']['biogas_rate_MJ_d']
    bio_kw = 1000*bio_mj_day/24/60/60
    hvac_params['bio_kw']=bio_kw
    hvac_params['t_rate']= (1/1000)*params['plants']['tsp_daymax_ml_pl_min']
    hvac_params['insolence']= (1/1000)*params['climate']['24hr_max']['irradiance_W_m2']
    building_l= params['structure']['building_L']
    building_w= params['structure']['building_W']
    systemw= params['structure']['width_m']
    systemh= params['structure']['height_m']
    roof_a = ((building_l+(2*systemw))*(building_w+(2*systemw)))-(building_l*building_w)
    wall_a = systemh*2*(building_l+building_w+(4*systemw))
    hvac_params['building_l']=building_l
    hvac_params['building_w']=building_w
    hvac_params['systemw']=systemw
    hvac_params['systemh']=systemh
    hvac_params['roof_a']=roof_a
    hvac_params['wall_a']=wall_a
    hvac_params['i_temp_d']=273.15+params['climate']['pro_day_C']
    hvac_params['i_temp_n']=273.15+params['climate']['pro_night_C']
    hvac_params['a_temp_d']=273.15+params['climate']['amb_day_C']
    hvac_params['a_temp_n'] = 273.15+params['climate']['amb_night_C']
    hvac_params['i_humidity_d']=(1/100)*params['climate']['pro_day_RH']
    hvac_params['i_humidity_n']=(1/100)*params['climate']['pro_night_RH']
    hvac_params['a_humidity_d'] = (1 / 100) * params['climate']['amb_day_RH']
    hvac_params['a_humidity_n'] = (1 / 100) * params['climate']['amb_night_RH']
    hvac_params['weeks_on']=params['plants']['weeks_on']
    hvac_params=hvac.update(hvac_params)
    return hvac_params


def conveyor_update(params):
    conveyor_params=params['conveyor'].copy()
    conveyor_params['prices'].update(params['prices'])
    floors=params['structure']['num_floors']
    conveyor_params['op_hours']=params['robot']['op_hours']
    conveyor_params['floors']=floors
    conveyor_params['num_towers']=(params['tower']['num_towers'])/floors
    conveyor_params['building_l']=params['structure']['building_L']
    conveyor_params['building_w']=params['structure']['building_W']
    conveyor_params['systemw']=params['structure']['width_m']
    conveyor_params['prices']=params['prices'].copy()
    conveyor_params['weeks_on']=params['plants']['weeks_on']
    conveyor_params=conveyor.update(conveyor_params)
    return conveyor_params


def nutrients_update(case_params):
    case = case_params['nutrients'].copy()
    case['prices']['electricity_kwh'] = case_params['prices']['electricity_kwh']
    case['supply_N_gpd'] = case_params['plants']['total_n_g_d']
    case_params['nutrients'] = digester.update(case)

def nursery_update(params):
    nursery = params['nursery'].copy()
    prices = nursery['prices']
    seed_per_tray = nursery['seed_per_tray']
    trays_per_rack = nursery['trays_per_rack']
    survival_pct = nursery['seed_survival_pct']
    seed_per_rack = seed_per_tray*trays_per_rack
    num_plants = params['tower']['num_plants']
    num_seeds = int(num_plants/survival_pct)
    num_racks = math.ceil(num_seeds*1/seed_per_tray*1/trays_per_rack)
    num_trays= num_racks*trays_per_rack
    germ_wk = params['plants']['germination_wk']
    capex = {} ; opex = {} ; energy = {}
    energy['total_kW'] = num_trays*nursery['LED_W_per_tray']/1000
    opex['seed'] = num_seeds*prices['seed_cost_USD']
    opex['LED'] = energy['total_kW']*params['prices']['electricity_kwh']*24*7*germ_wk
    opex['total_USD'] = sum([opex[x] for x in opex if not x == 'total_USD'])
    capex['total_USD'] = num_racks*prices['rack_cost_USD']
    nursery['num_trays'] = num_trays
    nursery['num_racks'] = num_racks
    nursery['opex'] = opex
    nursery['capex'] = capex
    nursery['energy'] = energy

    return nursery

def maintenance_update(params):
    global case_params
    maint = case_params['maintenance'].copy()
    maint['prices'] = case_params['prices'].copy()

    A_m2 = params['structure']['facade_GFA']
    N_1000m2 = math.ceil(A_m2/1000)
    num_towers = params['tower']['num_towers']

    tower_hrs = maint['hours_per_tower']*num_towers
    digester_hrs = maint['digester_hrs_1000m2']*N_1000m2
    hvac_hrs = maint['hvac_hrs_1000m2']*N_1000m2
    robot_hrs = maint['robot_hrs_1000m2']*N_1000m2
    engineer_hrs = maint['engineer_hrs_1000m2']*N_1000m2

    unskilled_hrs = tower_hrs+digester_hrs+hvac_hrs+robot_hrs
    skilled_hrs = engineer_hrs

    labor_unsk_USD_hr = maint['prices']['labor_unsk_USD_hr']
    skill_premium = maint['prices']['labor_skill_premium']
    labor_USD = labor_unsk_USD_hr*(skilled_hrs*skill_premium+unskilled_hrs)

    maint['N_1000m2'] = N_1000m2
    maint['skilled_hrs'] = skilled_hrs
    maint['unskilled_hrs'] = unskilled_hrs
    maint['opex'] = {'total_USD':labor_USD}

    return maint

def financials_update(params):
    global case_params
    capex = case_params['capex'].copy()
    opex = case_params['opex'].copy()
    revenue = case_params['revenue'].copy()

    #capex
    capex['structure'] = params['structure']['capex']['structure_USD']
    capex['tower'] = params['tower']['capex']['towers_USD']
    capex['robot'] = params['robot']['capex']['total_usd']
    capex['nutrients'] = params['nutrients']['capex']['total_USD']
    capex['conveyor'] = params['conveyor']['capex']['total_usd']
    if case_params['hvac']['nv_dess_refr']=='dess':
        capex['hvac'] = params['hvac']['capex']['total_usd_dess']
    elif case_params['hvac']['nv_dess_refr']=='refr':
        capex['hvac'] = params['hvac']['capex']['total_usd_refr']
    else:
        capex['hvac'] = params['hvac']['capex']['circ_fans'] + \
                       params['hvac']['capex']['il_fans'] + params['hvac']['capex']['vents']
    capex['nursery'] = params['nursery']['capex']['total_USD']
    capex['total'] = sum([capex[x] for x in capex if not x == 'total'])

    #opex
    opex['tower'] = params['tower']['opex']['total']
    opex['robot'] = params['robot']['opex']['total_usd']
    opex['nutrients'] = params['nutrients']['opex']['total_USD']
    opex['conveyor']= params['conveyor']['opex']['total_usd']
    if case_params['hvac']['nv_dess_refr']=='dess':
        opex['hvac']= params['hvac']['opex']['total_usd_dess']
    elif case_params['hvac']['nv_dess_refr']=='refr':
        opex['hvac'] = params['hvac']['opex']['total_usd_refr']
    else:
        opex['hvac'] = params['hvac']['opex']['circ_fans']+params['hvac']['opex']['il_fans']
    opex['maintenance'] = params['maintenance']['opex']['total_USD']
    opex['nursery'] = params['nursery']['opex']['total_USD']
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
    kpi['opex_m2'] = kpi['opex']/kpi['facade_wall_area']
    kpi['capex_tower'] = kpi['capex']/kpi['num_towers']

    kpi['profit'] = kpi['revenue']-kpi['opex']
    if kpi['capex']>0:
        kpi['simple_return'] = kpi['profit']/kpi['capex']

    case_params['kpi'] = kpi