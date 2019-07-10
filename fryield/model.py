import pandas as pd
import numpy as np
from utils.toolkit import ParameterTable
import math

isloaded = False
params = None
tables = {}
stages = {}
psyield = {}
PKG_FOLDER = 'fryield/'
CONSTANTS = {'water_g_cm3':1,
            }
photosynthesis_parameters = {'dli':72,
                    'ccr':0.6,
                    'ps_eff':0.14,
                    }


plant_parameters = {'leaf_th_nm':150,
                    'leaf_SG':1.05,
                    'leaf_density_g_cm2':0.01575,
                    'molar_ratio_photonCO2':22/3,
                    'biomass_g_molCO2':120,
                    'biomass_water':0.75,
                    'fruit_g':40,
                    }

organs = {'veg':{'roots':0.35,'stalk':0.325,'leaves':0.325,'flower-fruit':0},
          'rep':{'roots':0.25,'stalk':0.275,'leaves':0.275,'flower-fruit':0.20},
        }

growth_parameters = {'veg':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0,'stalk':0.50},
                     'rep':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0.35,'stalk':0.50},
                     'fr_harvest_weeks':40,
                     'size_g':{'veg':500,'rep':1200},
                    }

table_filenames = {'params':'parameters.csv',
                   }

default_params = {}

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


def run():
    pass

def fruit_yield(dli,ccr,period='A',units='fruit',fr_wks=None,plant_g=None):
    #fr/pl
    global growth_parameters, photosynthesis_parameters, plant_parameters
    stage='rep'
    ps_eff=photosynthesis_parameters['ps_eff']
    biomass_g = plant_parameters['biomass_g_molCO2']
    fruit_g = plant_parameters['fruit_g']

    la_cm2 = leaf_area_cm2(stage=stage,plant_g=plant_g)
    ps_mpd = canopy_photosynthesis_rate(dli,ccr,ps_eff)
    wet_ass_gpd = biomass_g*ps_mpd*la_cm2*(1/100)**2
    sink_rep = growth_parameters[stage]['flower-fruit']
    fr_gpd = wet_ass_gpd*sink_rep
    if units =='fruit':
        fr_d = fr_gpd/fruit_g
    else:
        fr_d = fr_gpd
    if period == 'D':
        fryield = fr_d
    elif period == 'A':
        if fr_wks is None:
            fr_wks = growth_parameters['fr_harvest_weeks']
        fryield = fr_d*fr_wks/52
    return fryield


def leaf_area_cm2(wt=None,stage='rep',plant_g=None):
    if plant_g is None:
        plant_g = plant_mass(stage)
    if wt is None:
        wt = plant_organ_wt('leaf',stage)
    g_cm2 = leaf_density()
    leaf_g = plant_g*wt
    cm2 = leaf_g/g_cm2
    return cm2


def plant_organ_wt(organ='leaf',stage='rep'):
    global organs
    wt = organs[stage][organ]
    return wt


def plant_mass(stage='rep'):
    plant_g = growth_parameters['size_g'][stage]
    return plant_g


def canopy_photosynthesis_rate(dli,ccr,ps_eff):
    #mol/m2/d
    global plant_parameters
    n_ps = plant_parameters['molar_ratio_photonCO2']
    rate = dli*ccr*ps_eff/n_ps
    return rate


def sink_ratios(params=None,stg=None):
    global growth_parameters
    if params is None:
        if stg is None:
            stg = 'veg'
        params = growth_parameters[stg]
    ratios = {}
    ratios['loss'] = params['loss']
    ratios['roots'] = params['root_shoot']*(1-params['loss'])
    ratios['flower-fruit'] = params['flower-fruit']
    ratios['stalk'] = params['stalk']*(1-params['flower-fruit']-ratios['roots']-params['loss'])
    ratios['leaves'] = 1-ratios['stalk']-params['flower-fruit']-ratios['roots']-params['loss']
    return ratios


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

def leaf_sugars():
    pass


def update_psyield():
    global params, psyield
    

def update_stages():
    global params, stages
    def get_stg_factors(stage_label):
        factors = {}
        factors['hazard']= params.get('hazardrate_' + stage_label)
        factors['cycletime'] = params.get('cycletime_' + stage_label)
        return factors
    
    def get_stg_a_factor(factors):
        hazard = factors['hazard']
        cycletime = factors['cycletime']
        a = cycletime*math.exp(hazard*cycletime)
        return a

    stages['vegetative']= get_stg_factors('vegetative')
    stages['reproductive']= get_stg_factors('reproductive')
    for stg in stages:
        stages[stg]['a'] = get_stg_a_factor(stages[stg])
    a = sum([stages[stg]['a'] for stg in stages])
    for stg in stages:
        stages[stg]['weight'] = stages[stg]['a']/a
        
def load(refresh=False):
    global tables, table_filenames, isloaded, PKG_FOLDER, params
    if (not isloaded) or (isloaded and refresh):
        for tblName in table_filenames:
            tables[tblName] = pd.read_csv(PKG_FOLDER + table_filenames[tblName])
    params = ParameterTable(tables['params'])
    update_stages()
    isloaded = True
