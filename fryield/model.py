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
                    }

growth_parameters = {'veg':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0,'stalk':0.50},
                     'rep':{'loss':0.2,'root_shoot':0.35,'flower-fruit':0.35,'stalk':0.50},
                    }

table_filenames = {'params':'parameters.csv',
                   }

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
