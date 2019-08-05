import numpy as np
import math
from utils.num_methods import rk45_integrate1D
from utils.num_methods import newton
from utils import chemistry as chem
import psypy.psySI as si
from fryield import fvcb as fvcb

CONSTANTS = {'water_g_cm3':1,
             'MW_H2O':18.02,
             'enth_vap_kJ_kg':2260,
            }

STAT_GROUPS = ['24hr_avg','24hr_max','day_avg','night_avg']
STAT_FIELDS = ['T_C','RH','irradiance_W_m2','ppfd_umol_m2_s']

default_params = {'ps_max_molCO2_m2_d':0.17,
                  'mature_wks':8,
                  'wall_transmissivity':0.8,
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
                  'leaf_light_capture':0.37,
                  'tsp_pct_leaf_energy':0.6,
                  'water_stress':0,
                  'p_abs_kPa':101.325,
                  'gs_min_mol_m2_s':0.015,
                  'gs_max_mol_m2_s':0.3,
                  'Ci_ubar':230,
                  'Ci_min':30,
                  'Ca_ubar':370,
                  'gb_mol_m2_s':3,
                  'gb_rel':1.37,
                  'gs_rel':1.6,
                  'photon_energy_umol_J':2.1,
                  'conductance_tuning':1,
                  '24hr_avg': {},
                  '24hr_max': {},
                  'day_avg': {},
                  'night_avg': {},
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
    dm,days_maturity = dm_at_LAI_pct(**kwargs)
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


def dm_at_LAI_pct(LAI_pct,hfull=0.25,**kwargs):
    def LAI_wrapper(tf,kwargs):
        LAI_p = LAI_pct_max(tf,**kwargs)
        return LAI_p
    update_params()
    global case_params
    model_args = ['mature_wks']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    t_guess = kwargs['mature_wks']*7
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

def plant_assimilation_rate(T_C,RH,I,ppfd,**kwargs):
    pass


def plant_transpiration_rate(T_C,RH,I,ppfd,**kwargs):
    pass

def net_assimilation_rate(T_C,RH,I,ppfd,**kwargs):
    #umol_m2_s
    def assim_wrapper(A,kwargs):
        Ci_min = kwargs['Ci_min']
        Ca = kwargs['Ca_ubar'] ; gb = kwargs['gb_mol_m2_s']
        gb_rel = kwargs['gb_rel'] ; gs_rel = kwargs['gs_rel']
        vpd_kPa = vapor_pressure_deficit(T_C,RH)
        tsp = leaf_transpiration_rate_mmol_m2_s(I,**kwargs)
        gs = stomata_conductance_from_tsp(tsp,vpd_kPa,**kwargs)
        grad = A*(gb_rel/gb+gs_rel/gs)
        if grad>=Ca:
            Ci = Ci_min
            Ag = (Ca-Ci)*1/(gb_rel/gb+gs_rel/gs)
        else:
            Ci = Ca-grad
            Ag = fvcb.net_assimilation_rate(T_C,ppfd,Ci,**kwargs)
        residual = Ag-A
        return residual
    tol = 0.05 ; hfull=0.25
    update_params()
    global case_params
    model_args = ['Ci_ubar','Ci_min','Ca_ubar','gb_rel',
                  'gs_rel','gb_mol_m2_s']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    Ci0 = kwargs['Ci_ubar']
    A0 = fvcb.net_assimilation_rate(T_C,ppfd,Ci0,**kwargs)
    A_umol_m2_s = newton(assim_wrapper,0,A0,kwargs,hfull=hfull,tolerance=tol)[0]
    return A_umol_m2_s

def stomata_conductance_from_tsp(tsp_mmol_m2_s,vpd_kPa,**kwargs):
    #mol_m2_s
    update_params()
    global case_params
    model_args = ['gs_min_mol_m2_s','gs_max_mol_m2_s',
        'p_abs_kPa','conductance_tuning']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    gs_range = [kwargs['gs_min_mol_m2_s'],kwargs['gs_max_mol_m2_s']]
    f = kwargs['conductance_tuning']
    P_kPa = kwargs['p_abs_kPa']
    gs_mol_m2_s = f*tsp_mmol_m2_s*P_kPa/vpd_kPa*1/1000
    if gs_mol_m2_s<gs_range[0]:
        gs_mol_m2_s=gs_range[0]
    elif gs_mol_m2_s>gs_range[1]:
        gs_mol_m2_s=gs_range[1]
    return gs_mol_m2_s

def leaf_transpiration_rate_mmol_m2_s(I,**kwargs):
    update_params()
    global case_params
    model_args = ['tsp_pct_leaf_energy',
                  'leaf_light_capture',
                  'wall_transmissivity','water_stress']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    tx_wall = kwargs['wall_transmissivity']
    lcr = kwargs['tsp_pct_leaf_energy']
    tsp_pct = kwargs['tsp_pct_leaf_energy']
    theta = kwargs['water_stress']
    enth_vap = CONSTANTS['enth_vap_kJ_kg']
    MW = CONSTANTS['MW_H2O']
    tsp_W_m2 = I*tx_wall*lcr*tsp_pct*(1-theta)
    tsp_mmol_m2_s = tsp_W_m2*1/enth_vap*1000/MW
    return tsp_mmol_m2_s

def vapor_pressure_deficit(T_C,RH):
    #kPa
    update_params()
    global case_params
    P = case_params['p_abs_kPa']
    psat = chem.antoine_psat(T_C)*P
    vpd_kPa = psat*(1-RH)
    return vpd_kPa

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