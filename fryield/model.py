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
table_filenames = {'params':'parameters.csv',
                   }

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
