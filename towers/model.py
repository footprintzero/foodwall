import pandas as pd
import numpy as np
import math

pipe_IDs = {'0.5':1.6,'0.75':2,'1':25}
models = {'hueristic_friction_head':{'a':3,'v0':1.7,'hf0':2.3},
          'losses':{'nozzle':150,'height':25},
          }

tower = {'V_root_zone':8.65,
         'void_fraction':0.3,
         'F_pipe_vol':0.1,
         'field_saturation':0.15,
         'media_density_kg_L':0.39,
         'towers_per_pump':20,
         'pump_head_kPa':196,
         }

SUBGROUPS = ['prices','energy','capex','opex']

default_params = {'height_m': 2.8,
                  'width_m':1.5,
                  'facade_L':336,
                  'dia_cm': 21,
                  'plant_hw': 1,
                  'top_clearance_cm': 30,
                  'tsp_mL_pl_d': 220,
                  'irr_to_per_h': 1,
                  'tower_height_m': 2.5,
                  'plants_per_tray': 3,
                  'plant_spacing_cm': 65,
                  'plant_clearance_cm': 29,
                  'unit_length_m': 1.8,
                  'trays_per_tower': 4,
                  'plants_per_tower': 12,
                  'unit_growth_area_m2': 4.5,
                  'unit_floor_area_m2': 2.7,
                  'num_towers': 183,
                  'num_plants': 2196,
                  'total_growth_area_m2': 823.5,
                  'total_floor_area_m2': 494.1,
                  'planting_density_pl_m2': 2.667,
                  'prices':{'PVC_dia21cm_USD_m':40,'PVC_90elbow_USD':2.86,
                           'misc_item_USD':34,'acrylic_tray_USD':4.3,
                           'leca_ball_USD_L':0.14,'PVC_dia20mm_USD_m':2.18,
                           'electricity_kwh':0.18,'pump_USD':20},
                  'energy':{'irrigation_kwh_yr':1000},
                  'capex':{'towers_USD':40000,'unit_USD':200,
                           'unit_tower_USD':0,'unit_pipe_USD':0,
                           'unit_items_USD':0,'unit_pumps_USD':0},
                  'opex':{'total':0,'irrigation_USD_yr':130},
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
    c = case_params.copy()
    tower_height_m = get_tower_height_m(c['height_m'],c['top_clearance_cm'])
    trays_per_tower = get_trays_per_tower(tower_height_m, c['plant_spacing_cm'],c['plant_hw'])
    plants_per_tower = get_plants_per_tower(trays_per_tower,c['plants_per_tray'])
    unit_length_m = get_unit_length_m(c['dia_cm'],c['plant_spacing_cm'],c['plant_clearance_cm'])
    num_towers = total_towers(c['facade_L'] ,unit_length_m)
    num_plants = total_plants(num_towers,plants_per_tower)
    unit_growth_area_m2 = c['height_m']*unit_length_m
    unit_floor_area_m2 = c['width_m']*unit_length_m
    total_growth_area_m2 = num_towers*unit_growth_area_m2
    total_floor_area_m2 = num_towers*unit_floor_area_m2
    planting_density_pl_m2 = plants_per_tower/unit_growth_area_m2

    case_params['tower_height_m'] = tower_height_m
    case_params['trays_per_tower'] = trays_per_tower
    case_params['plants_per_tower'] = plants_per_tower
    case_params['unit_length_m'] = unit_length_m
    case_params['num_towers'] = num_towers
    case_params['num_plants'] = num_plants
    case_params['unit_growth_area_m2'] = unit_growth_area_m2
    case_params['unit_floor_area_m2'] = unit_floor_area_m2
    case_params['total_growth_area_m2'] = total_growth_area_m2
    case_params['total_floor_area_m2'] = total_floor_area_m2
    case_params['planting_density_pl_m2'] = planting_density_pl_m2

    financials_update(case_params)

def financials_update(params):
    global tower
    prices = params['prices'].copy()
    capex = params['capex'].copy()
    opex = params['opex'].copy()

    tower_tray_USD = tower_tray_cost_USD(prices,params['plants_per_tray'])
    media_per_tray_USD = dry_media_cost(price_L=prices['leca_ball_USD_L'],
        V_L=tower['V_root_zone'],void_fraction=tower['void_fraction'])
    empty_tower_USD = prices['PVC_dia21cm_USD_m']*params['tower_height_m']
    capex['unit_tower_USD'] = empty_tower_USD + \
                              (tower_tray_USD+media_per_tray_USD)*params['trays_per_tower']
    capex['unit_pipe_USD'] = 2*params['unit_length_m']*prices['PVC_dia20mm_USD_m']
    capex['unit_items_USD'] = prices['misc_item_USD']
    capex['unit_pumps_USD'] = 1/tower['towers_per_pump']*prices['pump_USD']

    unit_components = ['unit_tower_USD','unit_pipe_USD','unit_items_USD','unit_pumps_USD']
    capex['unit_USD'] = sum([capex[x] for x in unit_components])
    capex['towers_USD'] = capex['unit_USD']*params['num_towers']

    #opex
    num_towers = params['num_towers']
    irr_V_L = irrigation_volume()
    Q_LPM = irr_V_L*params['irr_to_per_h']*1/60
    irr_W = pump_power(H_kPa=tower['pump_head_kPa'],Q_LPM=Q_LPM)
    irrigation_kwh_yr = irr_W*24*365/1000*num_towers
    case_params['energy']['irrigation_kwh_yr'] = irrigation_kwh_yr
    opex['irrigation_USD_yr']=irrigation_kwh_yr*prices['electricity_kwh']
    opex['total'] = sum([opex[x] for x in opex if not x == 'total'])

    case_params['capex'] = capex
    case_params['opex'] = opex


def tower_tray_cost_USD(prices,plants_per_tray):
    tray = prices['acrylic_tray_USD']
    ports = prices['PVC_90elbow_USD']*plants_per_tray
    tray_cost = tray+ports
    return tray_cost


def dry_media_cost(price_L,V_L,void_fraction):
    media_L = V_L*(1-void_fraction)
    media_cost = media_L*price_L
    return media_cost


def total_plants(num_towers,plants_per_tower):
    return num_towers*plants_per_tower


def total_towers(facade_L,unit_length_m):
    return math.floor(facade_L/unit_length_m)


def get_unit_length_m(dia,spacing,clearance):
    return (spacing*2+dia+clearance)/100


def get_plants_per_tower(trays_per_tower,plants_per_tray):
    ppt = trays_per_tower*plants_per_tray
    return ppt


def get_trays_per_tower(tower_height_m,plant_spacing_cm,plant_hw):
    tpt = math.floor(tower_height_m * 100 / (plant_hw*plant_spacing_cm))
    return tpt


def get_tower_height_m(floor_height_m,clearance_cm):
    height_m = floor_height_m-clearance_cm/100
    return height_m


def pump_power(H_kPa,Q_LPM):
    W = H_kPa*1000*Q_LPM*1/60000
    return W    

def pipe_loss_analysis(N,tpump,l0,params=None):
    global pipe_IDs
    cases = [(n,b) for n in N for b in tpump]
    VIrr = irrigation_volume(params)
    Q0 = 1/60*VIrr
    Q = [Q0*30/c[1]*c[0] for c in cases]
    pid_cases = pipe_IDs
    pid_cases['0.25'] = pipe_IDs['0.5']*0.5
    H = [[pipe_friction(Q0*30/c[1]*c[0],pid_cases[pid],l0*c[0]) for c in cases] for pid in pid_cases]
    fields = dict(zip(list(pid_cases.keys()),H))
    fields['Q'] = Q
    fields['N'] = [c[0] for c in cases]
    fields['tpump'] = [c[1] for c in cases]
    df = pd.DataFrame(fields)
    return df

def irrigation_volume(p=None):
    global tower, case_params
    if p is None:
        p = tower
        p.update(case_params)
    VIrr = p['V_root_zone']*(p['void_fraction']+p['field_saturation'])*(1+
            p['F_pipe_vol'])*p['trays_per_tower']
    return VIrr

def pipe_friction(Q_LPM,ID_cm,L_m,model='hueristic'):
    #input : flow Q in LPM, pipe ID in cm, pipe length L in m
    #output : friction head : kPa
    head_factor = 2.3
    v = pipe_velocity(Q_LPM,ID_cm)    
    if model=='hueristic':
        head_factor = hueristic_friction_model(v)
    head = head_factor*L_m
    return head        

def hueristic_friction_model(v):
    #input : velocity v in m/s
    #output : friction head per unit length : Pa/m
    global models
    mdl = models['hueristic_friction_head']
    head_factor = mdl['a']*(v-mdl['v0']) + mdl['hf0']
    return head_factor

def pipe_velocity(Q_LPM,ID_cm):
    #input : flow Q in LPM, pipe ID in cm
    #output : velocity in m/s
    A = cross_sectional_area(ID_cm/100) # in m
    v = Q_LPM/A*1/60000
    return v

def cross_sectional_area(D):
    A = math.pi*0.25*D**2
    return A
