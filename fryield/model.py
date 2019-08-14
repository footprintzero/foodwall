import pandas as pd
import numpy as np
import math
from fryield import photosynthesis as ps
#from utils.toolkit import ParameterTable

tables = {}
report = None
PKG_FOLDER = 'fryield/'
table_filenames = {'params':'parameters.csv',
                   }

CONSTANTS = {'water_g_cm3':1,
            }

SUBGROUPS = ['prices','revenue']


plant_parameters = {'leaf_density_g_cm2':0.01575,
                    'molar_ratio_photonCO2':22/3,
                    'biomass_water':0.75,
                    'fruit_g':40,
                    'tsp_ratio_ml_molCO2':420,
                    }

organs = {'veg':{'roots':0.40,'stalk':0.33,'leaves':0.27,'flower-fruit':0},
          'rep':{'roots':0.45,'stalk':0.25,'leaves':0.15,'flower-fruit':0.15},
        }

growth_parameters = {'veg':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0,'stalk':0.50},
                     'rep':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0.35,'stalk':0.50},
                    }

biomass_sinks = {'loss':0.2,'roots':0.28,'stalk':0.12,'leaves':0.12,'fower-fruit':0.28}

default_params = {'prices':{'fruit_USD_kg':2.86},
                  'num_plants':2196,
                  'daylight_hpd':12,
                  'wall_transmissivity':0.8,
                  'ambient_climate':False,
                  'pull_climate_data':True,
                  'Ca_ubar':370,
                  'pro_day_C':30,
                  'pro_day_RH':80,
                  'pro_night_C':27,
                  'pro_night_RH':80,
                  'plant_spacing_cm': 65,
                  'fw0_g': 10,
                  'fw_mature_g':670,
                  'canopy_decay':0.75,
                  'leaf_light_capture':0.37,
                  'tsp_pct_leaf_energy':0.6,
                  'LAI_max': 3,
                  'LAI_pct': 0.8,
                  'leaf_allocation0': 0.5,
                  'leaf_allocation': 0.35,
                  'leaf_th_nm': 190,
                  'leaf_SG': 0.6,
                  'biomass_g_molCO2': 120,
                  'yield_loss': 0.15,
                  'growth_rep_flower-fruit':0.25,
                  'growth_rep_loss':0.20,
                  'growth_rep_root':0.40,
                  'growth_rep_total_n':0.04,
                  'harvest_extension':1,
                  'germination_wk':4,
                  'maintenance_wk':2,
                  'tsp_daymax_ml_pl_min':6,
                  'ps_dli': 72,
                  'ps_ccr': 0.6,
                  'ps_ps_eff':0.14,
                  'planting_density_pl_m2': 2.667,
                  'fr_harvest_wk':40,
                  'mature_wk':6,
                  'weeks_on':46,
                  'tower_dia_cm':21,
                  'plant_hw': 1,
                  'canopy_fill':0.75,
                  'hourly':{},
                  'capex':{},
                  'opex':{},
                  'revenue':{'fruit_sale_USD_yr':46000},
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
    global plant_parameters
    c = case_params.copy()
    #plant number and dimensions
    planting_density_pl_m2 = c['planting_density_pl_m2'] ; s_cm = c['plant_spacing_cm']
    tower_dia_cm = c['tower_dia_cm'] ; hw = c['plant_hw']; canopy_fill = c['canopy_fill']
    num_plants = c['num_plants'] ; leaf_g_L = c['leaf_SG']*1000

    #photosynthesis
    ps_case = update_photosynthesis(**c)
    rep_ps_rate_molCO2_pl_d = ps_case['rep_ps_rate_molCO2_pl_d']
    rep_ps_rate_molCO2_d = rep_ps_rate_molCO2_pl_d*num_plants

    #transpiration
    rep_tsp_mL_pl_d = ps_case['rep_tsp_mL_pl_d']
    rep_tsp_max_mL_pl_d = ps_case['rep_tsp_max_mL_pl_d']
    rep_tsp_L_d = rep_tsp_mL_pl_d*num_plants/1000
    rep_tsp_max_d = rep_tsp_max_mL_pl_d*num_plants/1000

    #morphology and size
    rep_leaf_area_cm2 = ps_case['LA_m2']*100**2
    leaf_g = leaf_density()*rep_leaf_area_cm2
    rep_canopy_density = canopy_leaf_density_g_L(leaf_g,canopy_fill,s_cm,tower_dia_cm,hw,leaf_g_L)
    rep_canopy_depth_cm = canopy_depth_cm(s_cm,tower_dia_cm,canopy_fill)
    rep_leaf_coverage_index = leaf_coverage_index(rep_leaf_area_cm2,planting_density_pl_m2)

    fw0_g = ps_case['fw0_g']
    fw_mature_g = ps_case['fw_mature_g']
    size_rep_g = fw_mature_g

    growth_wk = ps_case['mature_wk']
    fr_harvest_wk = ps_case['fr_harvest_wk']
    harvest_extension = c['harvest_extension']
    weeks_on = 1/harvest_extension*growth_wk+fr_harvest_wk

    #fruit yield
    rep_growth_params = growth_parameters['rep'].copy()
    rep_growth_params.update({'root_shoot':c['growth_rep_root'],
                              'loss': c['growth_rep_loss'],
                              'flower-fruit': c['growth_rep_flower-fruit'],
                              })
    gfr_pl_d_day = fruit_yield_g(rep_ps_rate_molCO2_pl_d,rep_growth_params)
    gfr_pl_d_year = gfr_pl_d_day*fr_harvest_wk/52
    fruit_kg_yr = gfr_pl_d_year*num_plants*365/1000
    yield_kg_m2_yr = gfr_pl_d_year*365/1000*planting_density_pl_m2

    rep_fruit_pl_d_day = gfr_pl_d_day/plant_parameters['fruit_g']
    fruit_pl_d_day = rep_fruit_pl_d_day*fr_harvest_wk/52

    #nutrients
    threel_g = fw0_g
    mature_g = size_rep_g
    germination_wk = c['germination_wk']
    size_factor = avg_size_factor(threel_g,mature_g,size_rep_g,fr_harvest_wk,germination_wk)
    rep_total_n_mg_pl_d = nutrients_mg_pl_d(rep_ps_rate_molCO2_pl_d)['total_n']
    total_n_g_d = rep_total_n_mg_pl_d*num_plants*size_factor/1000
    tsp_mL_pl_d = rep_tsp_mL_pl_d*size_factor

    #costs and revenue
    yield_loss = c['yield_loss']
    fruit_USD_kg = c['prices']['fruit_USD_kg']
    fruit_sale_USD_yr = fruit_USD_kg*fruit_kg_yr*(1-yield_loss)

    case_params['ps_rate_molCO2_m2_d'] = ps_case['ps_rate_molCO2_m2_d']
    case_params['rep_ps_rate_molCO2_pl_d'] = rep_ps_rate_molCO2_pl_d
    case_params['rep_ps_rate_molCO2_d'] = rep_ps_rate_molCO2_d
    case_params['rep_leaf_area_cm2'] = rep_leaf_area_cm2

    case_params['rep_canopy_density'] = rep_canopy_density
    case_params['rep_canopy_depth_cm'] = rep_canopy_depth_cm
    case_params['rep_leaf_coverage_index'] = rep_leaf_coverage_index
    case_params['ps_ps_eff'] = ps_case['ps_ps_eff']
    case_params['ps_dli'] = ps_case['ps_dli']
    case_params['ps_ccr'] = ps_case['ps_ccr']

    case_params['rep_tsp_mL_pl_d'] = rep_tsp_mL_pl_d
    case_params['rep_tsp_L_d'] = rep_tsp_L_d
    case_params['rep_tsp_max_d'] = rep_tsp_max_d
    case_params['tsp_mL_pl_d'] = tsp_mL_pl_d
    case_params['tsp_daymax_ml_pl_min'] = rep_tsp_max_mL_pl_d/(24*60)

    case_params['fr_harvest_wk'] = fr_harvest_wk
    case_params['mature_wk'] = growth_wk
    case_params['weeks_on'] = weeks_on

    case_params['gfr_pl_d_day'] = gfr_pl_d_day
    case_params['gfr_pl_d_year'] = gfr_pl_d_year
    case_params['fruit_kg_yr'] = fruit_kg_yr
    case_params['rep_fruit_pl_d_day'] = rep_fruit_pl_d_day
    case_params['fruit_pl_d_day'] = fruit_pl_d_day
    case_params['yield_kg_m2_yr'] = yield_kg_m2_yr

    case_params['rep_total_n_mg_pl_d'] = rep_total_n_mg_pl_d
    case_params['total_n_g_d'] = total_n_g_d

    case_params['revenue']['fruit_sale_USD_yr'] = fruit_sale_USD_yr

def update_photosynthesis(**kwargs):
    global case_params
    model_args = ['daylight_hpd', 'wall_transmissivity', 'ambient_climate',
                  'pull_climate_data', 'Ca_ubar','pro_day_C', 'pro_day_RH', 'pro_night_C',
                  'plant_spacing_cm','fw0_g', 'fw_mature_g', 'canopy_decay',
                  'leaf_light_capture','tsp_pct_leaf_energy', 'LAI_max', 'LAI_pct',
                  'leaf_allocation0', 'leaf_allocation','leaf_th_nm',
                  'leaf_SG','biomass_g_molCO2','hourly']

    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    ps_case = ps.update(**kwargs)

    #photosynthesis
    ps_rate_molCO2_m2_d = ps_case['24hr_avg']['ps_umolCO2_m2_s']*3600*24*10**-6
    rep_ps_rate_molCO2_pl_d = ps_case['24hr_avg']['ps_molCO2_pl_d']

    ppfd = ps_case['24hr_avg']['ppfd_umol_m2_s'] ;  LAI = ps_case['LAI_max']*ps_case['LAI_pct']
    k = ps_case['canopy_decay']
    canopy_factor = ps.extinction(k,LAI)
    ccr = canopy_factor*ps_case['leaf_light_capture']
    dli = ppfd*3600*24*10**-6
    ps_ps_eff = photosynthesis_efficiency(ps_rate_molCO2_m2_d,dli,ccr)

    ps_case['ps_rate_molCO2_m2_d'] = ps_rate_molCO2_m2_d
    ps_case['rep_ps_rate_molCO2_pl_d'] = rep_ps_rate_molCO2_pl_d
    ps_case['ps_ps_eff'] = ps_ps_eff
    ps_case['ps_dli'] = dli
    ps_case['ps_ccr'] = ccr

    #transpiration
    rep_tsp_mL_pl_d = ps_case['24hr_avg']['tsp_ml_pl_min']*60*24
    rep_tsp_max_mL_pl_d = ps_case['24hr_max']['tsp_ml_pl_min']*60*24

    ps_case['rep_tsp_mL_pl_d'] = rep_tsp_mL_pl_d
    ps_case['rep_tsp_max_mL_pl_d'] = rep_tsp_max_mL_pl_d

    #morphology and size
    growth_wk = ps_case['mature_wk']
    maintenance_wk = case_params['maintenance_wk']
    germination_wk = case_params['germination_wk']
    fr_harvest_wk = get_fr_harvest_weeks(growth=growth_wk,
            maintenance=maintenance_wk,germination=germination_wk)
    ps_case['fr_harvest_wk'] = fr_harvest_wk

    return ps_case

def get_fr_harvest_weeks(growth=6,maintenance=2,germination=4):
    global case_params
    harvest_extension = case_params['harvest_extension']
    harvest_wks = 52-1/harvest_extension*(maintenance+growth+germination)
    return harvest_wks

def nutrients_mg_pl_d(ps_molCO2_d,growth_params=None):
    nutrients = {'total_n':0}
    global growth_parameters, case_params
    if growth_params is None:
        growth_params = growth_parameters['rep'].copy()
    sinks = get_biomass_sinks(growth_params)
    growth = 1-sinks['loss']
    assim_g_d = get_assim_pl_d(ps_molCO2_d)
    for n in nutrients:
        if n == 'total_n':
            wt = case_params['growth_rep_total_n']*(1-plant_parameters['biomass_water'])
            nutrients['total_n'] = assim_g_d*growth*wt*1000
    return nutrients


def avg_size_factor(threel_g,mature_g,rep_g,fr_harvest_wk,germination_wk,size_skew=0.6):
    veg_wk = 52-germination_wk-fr_harvest_wk
    veg_size = ((1-size_skew)*threel_g+size_skew*mature_g)
    avg_size_factor = (veg_size/rep_g*veg_wk+fr_harvest_wk)/52
    return avg_size_factor


def fruit_yield_g(ps_molCO2_d,growth_params=None):
    global growth_parameters
    if growth_params is None:
        growth_params = growth_parameters['rep'].copy()
    sinks = get_biomass_sinks(growth_params)
    flfr = sinks['flower-fruit']
    assim_g_d = get_assim_pl_d(ps_molCO2_d)
    fruit_g_d = assim_g_d*flfr
    return fruit_g_d

def get_assim_pl_d(ps_molCO2_d):
    global case_params
    return ps_molCO2_d*case_params['biomass_g_molCO2']

def get_biomass_sinks(params):
    growth = 1- params['loss']
    roots = growth*params['root_shoot']
    flfr = growth*params['flower-fruit']
    stalk=(growth-roots-flfr)*params['stalk']
    leaves = growth-roots-flfr-stalk
    sinks = {'loss':params['loss'],
             'roots': roots,
             'stalk': stalk,
             'leaves': leaves,
             'flower-fruit': flfr,
             }
    return sinks

def transpiration_rate(ps_rate):
    #mL_m2_d
    global plant_parameters
    ts_ratio = plant_parameters['tsp_ratio_ml_molCO2']
    return ps_rate*ts_ratio


def canopy_photosynthesis_rate(dli,ccr,ps_eff):
    #molCO2/m2/d
    global plant_parameters
    n_ps = plant_parameters['molar_ratio_photonCO2']
    rate = dli*ccr*ps_eff/n_ps
    return rate

def photosynthesis_efficiency(ps_rate,dli,ccr):
    #absorbed energy / utilized energy
    global plant_parameters
    n_ps = plant_parameters['molar_ratio_photonCO2']
    ps_eff = n_ps*ps_rate/(dli*ccr)
    return ps_eff

def leaf_coverage_index(leaf_area_cm2,pl_density_pl_m2):
    pl_area_cm2 = 100**2/pl_density_pl_m2
    cv_index = leaf_area_cm2/pl_area_cm2
    return cv_index


def leaf_area_cm2(plant_g,stage='rep',wt=None):
    if wt is None:
        wt = plant_organ_wt('leaves',stage)
    g_cm2 = leaf_density()
    leaf_g = plant_g*wt
    cm2 = leaf_g/g_cm2
    return cm2


def plant_organ_wt(organ='leaves',stage='rep'):
    global organs
    wt = organs[stage][organ]
    return wt


def leaf_density(th_um=None,sg=None):
    #g/cm2
    global CONSTANTS, plant_parameters, case_params
    if th_um is None:
        th_um = case_params['leaf_th_nm']
    if sg is None:
        sg = case_params['leaf_SG']
    th_cm = th_um*10**-4
    g_cm2 = CONSTANTS['water_g_cm3']*sg*th_cm #g/cm3*cm =  g/cm2
    return g_cm2

def canopy_leaf_density_g_L(leaf_g,canopy_fill,s_cm,dia_cm,hw,leaf_g_L):
    v_L = canopy_volume_L(canopy_fill,s_cm,dia_cm,hw)
    leaf_L = leaf_g/leaf_g_L
    return leaf_L/v_L

def canopy_volume_L(canopy_fill,s_cm,dia_cm,hw):
    h = hw*s_cm
    b_min = 0.5*(1/math.pi*4*s_cm-dia_cm)
    b = s_cm-canopy_fill*(s_cm-b_min)
    return 0.25*math.pi*(s_cm**2-b**2)*h*(1/100)**3*1000

def canopy_depth_cm(s_cm,dia_cm,canopy_fill):
    b_min=0.5*(4*s_cm/math.pi-dia_cm)
    return canopy_fill*(s_cm-b_min)