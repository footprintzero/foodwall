import numpy as np
import math
from utils.num_methods import rk45_integrate1D
from utils.num_methods import newton
from utils import chemistry as chem
import psypy.psySI as si
from fryield import fvcb as fvcb
from design import climate as climate

CONSTANTS = {'water_g_cm3':1,
             'MW_H2O':18.02,
             'enth_vap_kJ_kg':2260,
            }

STAT_GROUPS = ['24hr_avg','24hr_max','day_avg','night_avg']
STAT_FIELDS = ['T_C','RH','irradiance_W_m2','ppfd_umol_m2_s']
SUBGROUPS = [] + STAT_GROUPS

default_params = {'ps_max_molCO2_m2_d':0.17,
                  'tsp_daymax_ml_pl_min':2.69,
                  'LA_m2':1.33,
                  'pro_day_C':30,
                  'pro_day_RH':80,
                  'pro_night_C':27,
                  'pro_night_RH':80,
                  'mature_wk':8,
                  'fw0_g': 10,
                  'fw_mature_g':670,
                  'plant_spacing_cm': 65,
                  'canopy_decay':0.75,
                  'leaf_light_capture':0.37,
                  'tsp_pct_leaf_energy':0.6,
                  'LAI_max': 3,
                  'LAI_pct': 0.8,
                  'leaf_allocation0': 0.5,
                  'leaf_allocation': 0.35,
                  'Ca_ubar':370,
                  'ambient_climate':True,
                  'pull_climate_data':True,
                  'daylight_hpd':12,
                  'wall_transmissivity':0.8,
                  'leaf_th_nm':110,
                  'leaf_SG':0.6,
                  'biomass_g_molCO2':120,
                  'A_m2': 0.42,
                  'water_stress':0,
                  'p_abs_kPa':101.325,
                  'gs_min_mol_m2_s':0.015,
                  'gs_max_mol_m2_s':0.3,
                  'Ci_ubar':230,
                  'Ci_min':30,
                  'gb_mol_m2_s':3,
                  'gb_rel':1.37,
                  'gs_rel':1.6,
                  'photon_energy_umol_J':2.1,
                  'conductance_tuning':1,
                  'hourly': {},
                  '24hr_avg': {},
                  '24hr_max': {},
                  'day_avg': {},
                  'night_avg': {},
                 }

case_params = {}

def setup():
    global case_params
    case_params = default_params.copy()

def update(**params):
    global SUBGROUPS
    setup()
    if len(params)>0:
        for p in params:
            if p in SUBGROUPS:
                for s in params[p]:
                    case_params[p][s] = params[p][s]
            else:
                case_params[p] = params[p]
    run(**params)
    return case_params.copy()


def run(**kwargs):
    global case_params
    model_args = ['pull_climate_data']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    pull = kwargs['pull_climate_data']
    if pull:
        pull_climate_data()
    set_leaf_daily_avg(**kwargs)
    set_plant_daily_stats(**kwargs)

"""
    model adapted from literature reference :
    Goudriaan - expolinear growth equation to analyze resource capture
"""

def set_leaf_daily_avg(**kwargs):
    fields = STAT_FIELDS + ['tsp_mmol_m2_s', 'ps_umolCO2_m2_s']
    set_leaf_hourly(**kwargs)
    set_daily_stats_from_hourly(fields)

def mature_growth(**kwargs):
    global case_params
    model_args = ['LAI_pct']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    LAI_pct = kwargs['LAI_pct']
    fw,days_maturity = fw_at_LAI_pct(**kwargs)
    return (fw,days_maturity)

def fw_at_t(tf,**kwargs):
    global case_params
    model_args = ['fw0_g','A_m2','leaf_allocation0','leaf_allocation']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    A_m2 = kwargs['A_m2']
    fw0 = kwargs['fw0_g']/A_m2
    kw3 = kwargs.copy()
    kw3['leaf_allocation'] = 0.5*(kwargs['leaf_allocation0']+kwargs['leaf_allocation'])
    LAI0 = LAI_from_w(fw0,stage='initial',**kwargs)
    LAI = LAI_at_t(tf,LAI0,stage='final',**kwargs)
    fw = fw_from_LAI(LAI,**kw3)*A_m2
    return fw


def fw_at_LAI_pct(LAI_pct,hfull=0.25,pct_min=0.2,pct_max=0.8,**kwargs):
    def LAI_wrapper(tf,kwargs):
        LAI_p = LAI_pct_max(tf,**kwargs)
        return LAI_p
    global case_params
    model_args = ['mature_wk']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    t_guess = kwargs['mature_wk']*7*0.3
    result = newton(LAI_wrapper,LAI_pct,t_guess,kwargs,hfull=hfull,ymin=pct_min,ymax=pct_max)
    tf = result[0]
    fw = fw_at_t(tf,**kwargs)
    return (fw,tf)


def LAI_pct_max(tf,**kwargs):
    global case_params
    model_args = ['fw0_g','plant_spacing_cm','LAI_max']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    s_cm = kwargs['plant_spacing_cm']
    A_m2 = plant_area_from_spacing(s_cm)
    fw0 = kwargs['fw0_g']/A_m2
    LAI0 = LAI_from_w(fw0,**kwargs)
    LAI_max = kwargs['LAI_max']
    LAI = LAI_at_t(tf,LAI0,**kwargs)
    pct = LAI/LAI_max
    case_params['A_m2'] = A_m2
    return pct

def plant_area_from_spacing(spacing_cm):
    A_m2 = math.pi*(spacing_cm/100)**2
    return A_m2

def LAI_at_t(tf,LAI0,**kwargs):
    def dydt(t,y):
        rate = LAI_growth_rate_d(y,**kwargs)
        return rate

    LAI = rk45_integrate1D(dydt,0,tf,LAI0)
    return LAI


def set_initial_LAI():
    global case_params
    fw0 = case_params['fw0_m2']/case_params['A_m2']
    LAI0 = LAI_from_w(fw0)
    case_params['LAI0'] = LAI0


def fw_from_LAI(LAI,stage='final',**kwargs):
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
    fw = LAI*1/(s*pl)
    return fw


def LAI_from_w(w_g,stage='final',**kwargs):
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

def extinction(k,L):
    return 1-math.exp(-k*L)

def LAI_growth_rate_d(LAI,**kwargs):
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

def set_plant_daily_stats(**kwargs):
    global case_params
    kwargs['ps_max_molCO2_m2_d'] = case_params['24hr_avg']['ps_umolCO2_m2_s']*3600*24*10**-6
    (size_g, days) = mature_growth(**kwargs)
    kwargs['mature_wk'] = days/7
    kwargs['fw_mature_g'] = size_g
    case_params['mature_wk'] = kwargs['mature_wk']
    case_params['fw_mature_g'] = kwargs['fw_mature_g']
    LA_m2 = leaf_area_to_plant(**kwargs)
    case_params['LA_m2'] = LA_m2
    MW_H2O = CONSTANTS['MW_H2O']
    daily = {}
    for stat in STAT_GROUPS:
        daily[stat] = case_params[stat].copy()
        daily[stat]['ps_molCO2_pl_d'] = daily[stat]['ps_umolCO2_m2_s']*LA_m2*3600*24*10**-6
        daily[stat]['tsp_ml_pl_min'] = daily[stat]['tsp_mmol_m2_s']*LA_m2*MW_H2O*60*10**-3
        case_params[stat] = daily[stat]


def set_daily_stats_from_hourly(fields,**kwargs):
    global case_params
    model_args = ['daylight_hpd','pro_day_C','ambient_climate',
                  'pro_day_RH','pro_night_C','pro_night_RH']

    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    amb = kwargs['ambient_climate']
    pro_T_C = (kwargs['pro_day_C'],kwargs['pro_night_C'])
    pro_RH = (kwargs['pro_day_RH'],kwargs['pro_night_RH'])
    hourly = case_params['hourly']
    daylight_hpd = kwargs['daylight_hpd']
    morning_hr = 12-int(0.5*daylight_hpd)
    evening_hr = 12+int(0.5*daylight_hpd)
    day24hr_avg = [] ; day24hr_max = []
    day_avg = [] ; night_avg = []
    for stat in fields:
        if (stat in ['T_C','RH']) and (not amb):
            if stat=='T_C':
                day24hr_avg = 1/24*(daylight_hpd*pro_T_C[0]+(24-daylight_hpd)*pro_T_C[1])
                day24hr_max = max(pro_T_C)
                day_avg = pro_T_C[0] ; night_avg = pro_T_C[1]
            elif stat=='RH':
                day24hr_avg = 1/24*(daylight_hpd*pro_RH[0]+(24-daylight_hpd)*pro_RH[1])
                day24hr_max = max(pro_RH)
                day_avg = pro_RH[0] ; night_avg = pro_RH[1]
        else:
            day24hr_avg = sum(hourly[stat]) / 24
            day24hr_max = max(hourly[stat])
            day_avg = sum(hourly[stat][morning_hr:evening_hr]) / daylight_hpd
            night_avg = (sum(hourly[stat][:morning_hr])
                         + sum(hourly[stat][evening_hr:])) / (24 - daylight_hpd)
        case_params['24hr_avg'][stat] = day24hr_avg
        case_params['24hr_max'][stat] = day24hr_max
        case_params['day_avg'][stat] = day_avg
        case_params['night_avg'][stat] = night_avg
    if not amb:
        for stat in STAT_GROUPS:
            I = case_params[stat]['irradiance_W_m2'] ;  T_C = case_params[stat]['T_C']
            RH = case_params[stat]['RH'] ; ppfd = case_params[stat]['ppfd_umol_m2_s']
            case_params[stat]['ps_umolCO2_m2_s'] = net_assimilation_rate(T_C,RH/100,I,ppfd,**kwargs)


def set_leaf_hourly(**kwargs):
    global case_params
    hourly = case_params['hourly'].copy()
    if len(hourly)>0:
        hours = range(1,24)
        T_C = hourly['T_C']
        RH = hourly['RH']
        I = hourly['irradiance_W_m2']
        ppfd = hourly['ppfd_umol_m2_s']
        tsp_mmol_m2_s = [leaf_transpiration_rate_mmol_m2_s(I[i],**kwargs) for i in range(len(hours))]
        A_umol_m2_s = [net_assimilation_rate(T_C[i],
                RH[i]/100,I[i],ppfd[i],**kwargs) for i in range(len(hours))]
        hourly['tsp_mmol_m2_s'] = tsp_mmol_m2_s
        hourly['ps_umolCO2_m2_s'] = A_umol_m2_s
        case_params['hourly'] = hourly

def pull_climate_data():
    global case_params
    climate_case = climate.update()
    for grp in STAT_GROUPS+['hourly']:
        case_params[grp] = climate_case[grp].copy()

def leaf_area_to_plant(**kwargs):
    global case_params
    model_args = ['canopy_decay','LAI_max','LAI_pct','A_m2']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    LAI = kwargs['LAI_max']*kwargs['LAI_pct']
    k = kwargs['canopy_decay'] ; A_m2 = kwargs['A_m2']
    f = extinction(k,LAI)
    plant_factor = f*A_m2
    return plant_factor


def plant_assimilation_rate(T_C,RH,I,ppfd,**kwargs):
    #umol_pl_s
    leaf_m2_s = net_assimilation_rate(T_C,RH,I,ppfd,**kwargs)
    plant_factor = leaf_area_to_plant(**kwargs)
    pl_umol_s = leaf_m2_s*plant_factor
    return pl_umol_s


def plant_transpiration_rate(I,**kwargs):
    #mmol_pl_s
    leaf_m2_s = leaf_transpiration_rate_mmol_m2_s(I,**kwargs)
    plant_factor = leaf_area_to_plant(**kwargs)
    pl_mmol_s = leaf_m2_s*plant_factor
    return pl_mmol_s

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
    global case_params
    model_args = ['Ci_ubar','Ci_min','Ca_ubar','gb_rel',
                  'gs_rel','gb_mol_m2_s','wall_transmissivity']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    Ci0 = kwargs['Ci_ubar']
    tx_wall = kwargs['wall_transmissivity']
    A0 = fvcb.net_assimilation_rate(T_C,ppfd*tx_wall,Ci0,**kwargs)
    A_umol_m2_s = newton(assim_wrapper,0,A0,kwargs,hfull=hfull,tolerance=tol)[0]
    return A_umol_m2_s

def stomata_conductance_from_tsp(tsp_mmol_m2_s,vpd_kPa,**kwargs):
    #mol_m2_s
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