import fryield.model as plants
import pyppfd.solar as light
import robot.model as rbt
import towers.model as tower
import pandas as pd

cases = []
report = None

default_params = {'light':{},
          'tower':{},
          'plants':{'fr_harvest_weeks':40,'yield_units':'g'},
          'robot':{},
          'config':{'period':'A'},
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

def run():
    light.update(case_params['light'])
    tower.update(case_params['tower'])
    plants.update(case_params['plants'])
    robot_update()


def robot_update(case_params):
    plant_params = case_params['plants'].copy()
    plant_params['yield_units'] = 'fruit'
    fryield = get_fruit_yield(plant_params)
    case_params['robot']['fruit_plant_day'] = fryield
    rbt.update(case_params['robot'])


def get_fruit_yield(params=None):
    #fr/pl/d
    global case_params
    period = case_params['config']['period']
    if 'fr_harvest_weeks' in params:
        fr_wks = params['fr_harvest_weeks']
    if 'units' in params:
        units = params['units']
    dli = light.day_light_integral()
    tss = tower.greenhouse_transmissivity()
    ccr = tower.leaf_ccr()
    fryield = plants.fruit_yield(dli*tss,ccr,period,units,fr_wks)
    return fryield


def get_ps_rate():
    dli = light.day_light_integral()
    tss = tower.greenhouse_transmissivity()
    ccr = tower.leaf_ccr()
    ps_rate = plants.canopy_photosynthesis_rate(dli*tss,ccr)
    return ps_rate
