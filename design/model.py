import pyppfd.solar as light
import structure.model as structure
import towers.model as tower
import fryield.model as plants
import robot.model as rbt
import hvac.model as hvac
import conveyor.model as conveyor
import nutrients.digester as digester
import pandas as pd

cases = []
report = None

default_params = {'light':{'angle_max':90,'cloud_cover':0.25,
                           'daylight_hrs':10,'ps_dli':72,'insolence_W_m2':335},
          'climate':{'amb_day_C':32,'amb_night_C':27,'pro_day_C':27,'pro_day_RH':75,
                     'amb_day_RH':70,'amb_night_RH':85,'pro_night_C':25,'pro_night_RH':85,
                     'rainfall_mm_wk':40,
                     '24hr_avg':{},'24hr_max':{},'day_avg':{},'night_avg':{}},
          'prices':{'electricity_kwh':0.18,'fruit_USD_kg':2.86},
          'structure':{'num_floors':1,'height_m':2.8,'building_L':150,'building_W':15},
          'tower':{'plant_spacing_cm':62,'plant_clearance_cm':35},
          'plants':{'leaf_ccr':0.6,'fr_harvest_weeks':40,'rep_growth':0.25,
                    'tsp_mL_pl_d':220,'tsp_max_daily':4},
          'robot':{'num_towers': 186,'trays_per_tower': 4,'fruit_pl_d_day': .56},
          'conveyor':{'num_towers':186,'rpd':20,'weeks_on':40},
          'hvac':{'f_hvac_cfm':40000,'bio_kw':66.218,'t_rate':.00296,'num_towers':186,'weeks_on':40,
                  'true_for_dess':True},
          'nutrients':{'N_recovery':0.5,'supply_N_gpd':1084,
                       'biogas_yield_kJ_g':9.88,
                       'AN_capacity_factor_kgpd_m3':10,
                       'prices':{'thermal_energy_discount':0.9,
                                 },
                       },
          'maintenance':{},
          'config':{'period':'A'},
          'capex':{'total':750000,'structure':0,'tower':0,'conveyor':100000,
                   'robot':0,'hvac':100000,'nutrient':100000},
          'opex':{'total':12000,'structure':0,'tower':0,'conveyor':3000,
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
    case_params = default_params.copy()


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
    case_params['tower'] = tower_update(case_params) #for structure
    case_params['plants'] = plants_update(case_params)
    case_params['tower'] = tower_update(case_params) #for irrigation
    case_params['robot'] = robot_update(case_params)
    case_params['conveyor']= conveyor_update(case_params)

    nutrients_update(case_params)
    case_params['hvac'] = hvac_update(case_params)
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
    tsm = params['structure']['wall_transmissivity']
    plants_params['ps_dli'] = tsm*params['light']['ps_dli']

    #climate
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


def hvac_update(params):
    hvac_params = params['hvac'].copy()
    floors=params['structure']['num_floors']
    hvac_params['floors']=floors
    hvac_params['num_towers'] = (params['tower']['num_towers'])/floors
    hvac_params['p_tower'] = 3*params['tower']['trays_per_tower']
    bio_mj_day = params['nutrients']['biogas_rate_MJ_d']
    bio_kw = 1000*bio_mj_day/24/60/60
    hvac_params['bio_kw']=bio_kw
    hvac_params['t_rate']= (1/1000)*params['plants']['tsp_max_daily']
    hvac_params['insolence']= (1/1000)*params['light']['insolence_W_m2']
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
    hvac_params['weeks_on']=params['plants']['fr_harvest_weeks']
    hvac_params['prices']=params['prices'].copy()
    hvac_params=hvac.update(hvac_params)
    return hvac_params


def conveyor_update(params):
    conveyor_params=params['conveyor'].copy()
    floors=params['structure']['num_floors']
    conveyor_params['floors']=floors
    conveyor_params['num_towers']=(params['tower']['num_towers'])/floors
    conveyor_params['building_l']=params['structure']['building_L']
    conveyor_params['building_w']=params['structure']['building_W']
    conveyor_params['systemw']=params['structure']['width_m']
    conveyor_params['kw_price']=params['prices']['electricity_kwh']
    conveyor_params['weeks_on']=params['plants']['fr_harvest_weeks']
    conveyor_params=conveyor.update(conveyor_params)
    return conveyor_params


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
    capex['conveyor'] = params['conveyor']['capex']['total_usd']
    if params['hvac']['true_for_dess']:
        capex['hvac'] = params['hvac']['capex']['total_usd_dess']
    else:
        capex['hvac'] = params['hvac']['capex']['total_usd_refr']
    capex['total'] = sum([capex[x] for x in capex if not x == 'total'])

    #opex
    opex['tower'] = params['tower']['opex']['total']
    opex['robot'] = params['robot']['opex']['total_USD']
    opex['nutrients'] = params['nutrients']['opex']['total_USD']
    opex['conveyor']= params['conveyor']['opex']['total_usd']
    if case_params['hvac']['true_for_dess']:
        opex['hvac']= params['hvac']['opex']['total_usd_dess']
    else:
        opex['hvac'] = params['hvac']['opex']['total_usd_refr']
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