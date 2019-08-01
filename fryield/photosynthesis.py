import numpy as np
import math
from utils.num_methods import rk45_integrate1D
from utils.num_methods import newton

CONSTANTS = {'water_g_cm3':1,
            }

default_params = {'ps_max_molCO2_m2_d':0.17,
                  'biomass_g_molCO2':120,
                  'canopy_decay':0.75,
                  'dm0_g': 2.5,
                  'A_m2': 1.7,
                  'LAI_max': 3,
                  'LAI_pct': 0.8,
                  'leaf_allocation0': 0.5,
                  'leaf_allocation': 0.35,
                  'leaf_th_nm':110,
                  'leaf_SG':0.6,
                  }

case_params = {}


def update_params(params=None):
    global case_params
    if len(case_params)==0:
        case_params = default_params.copy()
        if not params is None:
            for p in params:
                case_params[p] = params[p]

def run(params=None):
    update_params(params)
    #
    #
    #

"""
    model adapted from literature reference :
    Goudriaan - expolinear growth equation to analyze resource capture
"""

def mature_growth(**kwargs):
    update_params()
    global case_params
    model_args = ['LAI_pct']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    LAI_pct = kwargs['LAI_pct']
    dm,days_maturity = growth_at_LAI_pct(**kwargs)
    return (dm,days_maturity)

def dm_at_t(tf,**kwargs):
    update_params()
    global case_params
    model_args = ['dm0_g','A_m2','leaf_allocation0','leaf_allocation']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    A_m2 = kwargs['A_m2']
    dm0 = kwargs['dm0_g']/A_m2
    kw3 = kwargs.copy()
    kw3['leaf_allocation'] = 0.5*(kwargs['leaf_allocation0']+kwargs['leaf_allocation'])
    LAI0 = LAI_from_w(dm0,stage='initial',**kwargs)
    LAI = LAI_at_t(tf,LAI0,stage='final',**kwargs)
    dm = dm_from_LAI(LAI,**kw3)*A_m2
    return dm


def growth_at_LAI_pct(LAI_pct,t_guess=80,hfull=0.25,**kwargs):
    def LAI_wrapper(tf,kwargs):
        LAI_p = LAI_pct_max(tf,**kwargs)
        return LAI_p
    result = newton(LAI_wrapper,LAI_pct,t_guess,kwargs,hfull=hfull)
    tf = result[0]
    dm = dm_at_t(tf,**kwargs)
    return (dm,tf)


def LAI_pct_max(tf,**kwargs):
    update_params()
    global case_params
    model_args = ['dm0_g','A_m2','LAI_max']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    A_m2 = kwargs['A_m2']
    dm0 = kwargs['dm0_g']/A_m2
    LAI0 = LAI_from_w(dm0,**kwargs)
    LAI_max = kwargs['LAI_max']
    LAI = LAI_at_t(tf,LAI0,**kwargs)
    pct = LAI/LAI_max
    return pct


def LAI_at_t(tf,LAI0,**kwargs):
    def dydt(t,y):
        rate = LAI_growth_rate_d(y,**kwargs)
        return rate

    LAI = rk45_integrate1D(dydt,0,tf,LAI0)
    return LAI


def set_initial_LAI():
    global case_params
    dm0 = case_params['dm0_m2']/case_params['A_m2']
    LAI0 = LAI_from_w(dm0)
    case_params['LAI0'] = LAI0


def dm_from_LAI(LAI,stage='final',**kwargs):
    update_params()
    global case_params
    model_args = ['leaf_allocation','leaf_allocation0','leaf_th_nm','leaf_SG']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    if stage=='initial':
        pl = kwargs['leaf_allocation0']
    else:
        pl = kwargs['leaf_allocation']
    th_um = kwargs['leaf_th_nm'] ; sg = kwargs['leaf_SG']
    g_m2 = leaf_density(th_um,sg)
    s = 1/g_m2
    dm = LAI*1/(s*pl)
    return dm


def LAI_from_w(w_g,stage='final',**kwargs):
    update_params()
    global case_params
    model_args = ['leaf_allocation','leaf_allocation0','leaf_th_nm','leaf_SG']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    if stage=='initial':
        pl = kwargs['leaf_allocation0']
    else:
        pl = kwargs['leaf_allocation']
    th_um = kwargs['leaf_th_nm'] ; sg = kwargs['leaf_SG']
    g_m2 = leaf_density(th_um,sg)
    s = 1/g_m2
    LAI = w_g*s*pl
    return LAI


def LAI_growth_rate_d(LAI,**kwargs):
    def extinction(k,L):
        return 1-math.exp(-k*L)
    update_params()
    global case_params
    model_args = ['biomass_g_molCO2','ps_max_molCO2_m2_d',
                  'canopy_decay','LAI_max',
                  'leaf_allocation','leaf_th_nm','leaf_SG']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    bm = kwargs['biomass_g_molCO2'] ; psm = kwargs['ps_max_molCO2_m2_d']
    k = kwargs['canopy_decay'] ;    Lm = kwargs['LAI_max']
    pl = kwargs['leaf_allocation']
    th_um = kwargs['leaf_th_nm'] ; sg = kwargs['leaf_SG']
    g_m2 = leaf_density(th_um,sg)
    s = 1/g_m2
    cm = psm*bm
    f = extinction(k,(Lm-LAI))/extinction(k,Lm)
    c = cm*extinction(k,LAI)
    growth_rate = pl*s*c*f
    return growth_rate


def leaf_density(th_um=None,sg=None):
    #g/m2
    global CONSTANTS, plant_parameters
    if th_um is None:
        th_um = plant_parameters['leaf_th_nm']
    if sg is None:
        sg = plant_parameters['leaf_SG']
    th_m = th_um*10**-6
    g_m2 = CONSTANTS['water_g_cm3']*sg*th_m*100**3
    return g_m2