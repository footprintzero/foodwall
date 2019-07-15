import pandas as pd
import numpy as np
import math
#from utils.toolkit import ParameterTable

tables = {}
report = None
PKG_FOLDER = 'fryield/'
table_filenames = {'params':'parameters.csv',
                   }

CONSTANTS = {'water_g_cm3':1,
            }

plant_parameters = {'leaf_th_nm':150,
                    'leaf_SG':1.05,
                    'leaf_density_g_cm2':0.01575,
                    'molar_ratio_photonCO2':22/3,
                    'biomass_g_molCO2':120,
                    'biomass_water':0.75,
                    'fruit_g':40,
                    'tsp_ratio_ml_molCO2':420,
                    }

organs = {'veg':{'roots':0.35,'stalk':0.325,'leaves':0.325,'flower-fruit':0},
          'rep':{'roots':0.25,'stalk':0.275,'leaves':0.275,'flower-fruit':0.20},
        }

growth_parameters = {'veg':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0,'stalk':0.50},
                     'rep':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0.35,'stalk':0.50},
                    }

biomass_sinks = {'loss':0.2,'roots':0.28,'stalk':0.12,'leaves':0.12,'fower-fruit':0.28}

default_params = {'ps_ccr':0.6,
                  'tower_dia_cm':21,
                  'planting_density_pl_m2': 2.667,
                  'plant_spacing_cm': 65,
                  'plant_hw': 1,
                  'ps_ps_eff':0.14,
                  'ps_dli': 72,
                  'growth_rep_flower-fruit':0.35,
                  'growth_rep_loss':0.20,
                  'growth_rep_root':0.35,
                  'growth_rep_total_n':0.015,
                  'fr_harvest_wk':40,
                  'germination_wk':4,
                  'num_plants':2196,
                  'amb_day_C':32,
                  'amb_day_RH':70,
                  'amb_night_C':27,
                  'amb_night_RH':85,
                  'size_3l_g':40,
                  'size_mature_g':800,
                  'size_rep_g':1200,
                  'tsp_max_daily':3,
                  'canopy_fill':0.75,
                  }

case_params = {}


def setup():
    global case_params, default_parameters
    case_params = default_params


def update(params=None):
    setup()
    if params is not None:
        for p in params:
            case_params[p] = params[p]
    run()
    return case_params.copy()


def run():
    global plant_parameters
    c = case_params.copy()
    #leaf area and morphology
    size_rep_g = c['size_rep_g'] ; planting_density_pl_m2 = c['planting_density_pl_m2']
    s_cm = c['plant_spacing_cm'] ; tower_dia_cm = c['tower_dia_cm'] ; hw = c['plant_hw']
    canopy_fill = c['canopy_fill']
    num_plants = c['num_plants']
    leaf_g_L = plant_parameters['leaf_SG']*1000
    rep_leaf_area_cm2 = leaf_area_cm2(size_rep_g,'rep')
    leaf_g = leaf_density()*rep_leaf_area_cm2
    rep_canopy_density = canopy_leaf_density_g_L(leaf_g,canopy_fill,s_cm,tower_dia_cm,hw,leaf_g_L)
    rep_canopy_depth_cm = canopy_depth_cm(s_cm,tower_dia_cm,canopy_fill)
    rep_leaf_coverage_index = leaf_coverage_index(rep_leaf_area_cm2,planting_density_pl_m2)

    #photosynthesis
    ps_rate_molCO2_m2_d = canopy_photosynthesis_rate(c['ps_dli'],c['ps_ccr'],c['ps_ps_eff'])
    rep_ps_rate_molCO2_pl_d = ps_rate_molCO2_m2_d*rep_leaf_area_cm2*(1/100)**2
    rep_ps_rate_molCO2_d = rep_ps_rate_molCO2_pl_d*num_plants

    #transpiration
    rep_tsp_mL_pl_d = transpiration_rate(rep_ps_rate_molCO2_pl_d)
    rep_tsp_L_d = rep_tsp_mL_pl_d*num_plants/1000
    rep_tsp_max_d = rep_tsp_L_d*c['tsp_max_daily']

    #fruit yield
    rep_growth_params = growth_parameters['rep'].copy()
    rep_growth_params.update({'root_shoot':c['growth_rep_root'],
                              'loss': c['growth_rep_loss'],
                              'flower-fruit': c['growth_rep_flower-fruit'],
                              })
    fr_harvest_wk= c['fr_harvest_wk']
    gfr_pl_d_day = fruit_yield_g(rep_ps_rate_molCO2_pl_d,rep_growth_params)
    gfr_pl_d_year = gfr_pl_d_day*fr_harvest_wk/52
    fruit_kg_yr = gfr_pl_d_year*num_plants*365/1000
    yield_kg_m2_yr = gfr_pl_d_year*365/1000*planting_density_pl_m2

    fruit_pl_d_day = gfr_pl_d_day/plant_parameters['fruit_g']
    fruit_plant_day = fruit_pl_d_day*fr_harvest_wk/52

    #nutrients
    threel_g = c['size_3l_g'] ;     mature_g = c['size_3l_g'] ; rep_g = c['size_rep_g']
    germination_wk = c['germination_wk']
    size_factor = avg_size_factor(threel_g,mature_g,rep_g,fr_harvest_wk,germination_wk)
    rep_total_n_mg_pl_d = nutrients_mg_pl_d(rep_ps_rate_molCO2_pl_d)['total_n']
    total_n_g_d = rep_total_n_mg_pl_d*num_plants*size_factor

    case_params['ps_rate_molCO2_m2_d'] = ps_rate_molCO2_m2_d
    case_params['rep_ps_rate_molCO2_pl_d'] = rep_ps_rate_molCO2_pl_d
    case_params['rep_leaf_area_cm2'] = rep_leaf_area_cm2
    case_params['rep_canopy_density'] = rep_canopy_density
    case_params['rep_canopy_depth_cm'] = rep_canopy_depth_cm
    case_params['rep_leaf_coverage_index'] = rep_leaf_coverage_index
    case_params['rep_tsp_mL_pl_d'] = rep_tsp_mL_pl_d
    case_params['rep_tsp_L_d'] = rep_tsp_L_d
    case_params['rep_tsp_max_d'] = rep_tsp_max_d

    case_params['gfr_pl_d_day'] = gfr_pl_d_day
    case_params['gfr_pl_d_year'] = gfr_pl_d_year
    case_params['fruit_kg_yr'] = fruit_kg_yr
    case_params['fruit_pl_d_day'] = fruit_pl_d_day
    case_params['fruit_plant_day'] = fruit_plant_day
    case_params['yield_kg_m2_yr'] = yield_kg_m2_yr

    case_params['rep_total_n_mg_pl_d'] = rep_total_n_mg_pl_d
    case_params['total_n_g_d'] = total_n_g_d

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
            wt = case_params['growth_rep_total_n']
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
    return ps_molCO2_d*plant_parameters['biomass_g_molCO2']

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
    global CONSTANTS, plant_parameters
    if th_um is None:
        th_um = plant_parameters['leaf_th_nm']
    if sg is None:
        sg = plant_parameters['leaf_SG']
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