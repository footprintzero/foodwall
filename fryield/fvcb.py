import math
from utils.num_methods import quadratic_roots

CONSTANTS = {'R_ig_J_K_mol':8.3145,
            }

default_params = {'leaf_energy_loss':0.23,
                  'molar_ratio_photonCO2': 22 / 3,
                  'dark_resp_25C_umol_m2_s': 1.1,
                  'dark_resp_Ha_J_mol': 66405,
                  'photon_flux_umol_m2_s': 1000,
                  'assimilation_molCO2_m2_s': 18.8,
                  'pCO2_intc_ubar':230,
                  'pCO2_amb_ubar':300,
                  'pO2_amb_mbar':210,
                  'carbox_conc_umol_gChl': 87,
                  'carbox_ox_ratio': 0.23,
                  'Vc_max_umol_m2_s': 98,
                  'CO2_comp_wo_resp_ubar': 31,
                  'CO2_comp_ubar': 40,
                  'leaf_energy_loss': 0.23,
                  'kc_carbox_turnover_s': 2.5,
                  'ko_ox_turnover_s': 0.525,
                  'm_PGA_red_max_umol_gChol_s': 436,
                  'chloroplast_density_g_m2': 0.45,
                  'carbox_ox_sel_c': -9.2, # Nicotiana tabacum Walker 2013 value -9.2
                  'carbox_ox_sel_dHa_J_mol': -36000, # adjusted -- Nicotiana tabacum Walker 2013 34,200 Jmol-1
                  'carbox_c': 17.5, #Nicotiana tabacum Walker 2013
                  'carbox_dHa_J_mol': 28200, # adjusted -- Nicotiana tabacum Walker 2013 37,600 Jmol-1
                  'ox_c': 15.3, #Nicotiana tabacum Walker 2013
                  'ox_dHa_J_mol': 24100, #Nicotiana tabacum Walker 2013
                  'kc_Ha_J_mol': 58520, #FvCB 1980
                  'kc_k25C_s': 2.5, #FvCB 1980
                  'hyperbolic_shape_factor': 20, #FvCB 1980
                  'j_max_j0_uEq_gChl_s': 1.466*10**9, # adjusted to match 467 umol_m2_s @ 25C FvCB 1980
                  'j_max_E_J_mol': 37000, #FvCB 1980
                  'j_max_H_J_mol': 220000, #FvCB 1980
                  'j_max_S_J_mol_K': 710, #FvCB 1980
                  }

case_params = {}


def update_params(params=None):
    global case_params
    if len(case_params)==0:
        case_params = default_params.copy()
        if not params is None:
            for p in params:
                case_params[p] = params[p]


def leaf_photosynthesis_efficiency(T_C,I,pCO2_ubar,**kwargs):
    update_params()
    global case_params
    model_args = ['molar_ratio_photonCO2']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    molar_ratio = kwargs['molar_ratio_photonCO2']
    A = net_assimilation_rate(T_C,I,pCO2_ubar,**kwargs)
    nu = A*molar_ratio/I
    return nu


def net_assimilation_rate(T_C,I,pCO2_ubar,**kwargs):
    #umol_m2_s
    vc = carboxylation_rate(T_C,I,pCO2_ubar,**kwargs)
    R = dark_resp(T_C,**kwargs)
    phi = phi_carbox_oxy(T_C,pCO2_ubar,**kwargs)
    A = (1-0.5*phi)*vc-R
    return A

def carboxylation_rate(T_C,I,pCO2_ubar,**kwargs):
    #umol_m2_s
    j = electron_transport(T_C,I,**kwargs)
    rup2_e13 = rup2_sat_rate_eqn_13(T_C,pCO2_ubar,**kwargs)
    rup2_e40 = rup2_sat_rate_eqn_40(T_C,pCO2_ubar,**kwargs)
    vc = min([j,rup2_e13,rup2_e40])
    return vc

def electron_transport(T_C,I,**kwargs):
    #umol_m2_s
    update_params()
    global case_params
    model_args = ['leaf_energy_loss','hyperbolic_shape_factor',
                  'chloroplast_density_g_m2']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    f = kwargs['leaf_energy_loss'] ;     Z = kwargs['hyperbolic_shape_factor']
    p = kwargs['chloroplast_density_g_m2']
    jmax = e_transport_max(T_C,**kwargs)
    Jmax = jmax*p   #convert from /gChl to /m2
    J_I = 0.5*(1-f)*I
    c = J_I*Jmax
    b = -1*(J_I+Jmax+Z)
    J = min(quadratic_roots(1,b,c))
    return J

def e_transport_max(T_C,**kwargs):
    #uEq_gChl_s
    update_params()
    global case_params
    model_args = ['j_max_j0_uEq_gChl_s','j_max_E_J_mol',
                  'j_max_H_J_mol','j_max_S_J_mol_K']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    j0 = kwargs['j_max_j0_uEq_gChl_s']
    E = kwargs['j_max_E_J_mol']
    H = kwargs['j_max_H_J_mol']
    S = kwargs['j_max_S_J_mol_K']
    R = CONSTANTS['R_ig_J_K_mol']
    invRT = 1/(R*T_K(T_C))
    denom = 1+math.exp(invRT*(S*T_K(T_C)-H))
    jmax = j0*math.exp(-E*invRT)/denom
    return jmax

def dark_resp(T_C,**kwargs):
    #umol_m2_s
    update_params()
    global case_params
    model_args = ['dark_resp_Ha_J_mol','dark_resp_25C_umol_m2_s']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    dHa = kwargs['dark_resp_Ha_J_mol']
    r25C = kwargs['dark_resp_25C_umol_m2_s']
    r = arrhenius(T_C,r25C,dHa)
    return r

def rup2_sat_rate_eqn_40(T_C,pCO2_ubar,**kwargs):
    update_params()
    global case_params
    model_args = ['Vc_max_umol_m2_s','pO2_amb_mbar']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    Vc_max = kwargs['Vc_max_umol_m2_s']
    pO2_mbar = kwargs['pO2_amb_mbar']
    gamma_no_dark = CO2_compensation_no_dark(T_C,**kwargs)
    Rd = dark_resp(T_C,**kwargs)
    Kc_ubar = K_carbox(T_C,**kwargs)
    Ko_mbar = K_ox(T_C,**kwargs)
    denom = pCO2_ubar+ Kc_ubar*(1+pO2_mbar/Ko_mbar)
    A = Vc_max*(pCO2_ubar-gamma_no_dark)/denom-Rd
    return A

def rup2_sat_rate_eqn_13(T_C,pCO2_ubar,**kwargs):
    #umol_m2_s
    update_params()
    global case_params
    model_args = ['pO2_amb_mbar','carbox_conc_umol_gChl',
                  'chloroplast_density_g_m2']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    p = kwargs['chloroplast_density_g_m2']
    Et = kwargs['carbox_conc_umol_gChl']
    pO2_mbar = kwargs['pO2_amb_mbar']
    kc_s = k_carbox(T_C,**kwargs)
    Kc_ubar = K_carbox(T_C,**kwargs)
    Ko_mbar = K_ox(T_C,**kwargs)
    denom = pCO2_ubar+Kc_ubar*(1+pO2_mbar/Ko_mbar)
    kprime = kc_s*pCO2_ubar/denom
    rate_umol_m2_s = kprime*Et*p
    return rate_umol_m2_s


def CO2_compensation(T_C,**kwargs):
    update_params()
    global case_params
    model_args = ['Vc_max_umol_m2_s','pO2_amb_mbar']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    Vc_max = kwargs['Vc_max_umol_m2_s']
    pO2_mbar = kwargs['pO2_amb_mbar']
    gamma_no_dark = CO2_compensation_no_dark(T_C,**kwargs)
    Kc = K_carbox(T_C,**kwargs) ; Ko = K_ox(T_C,**kwargs)
    Rd = dark_resp(T_C,**kwargs)
    denom = 1-Rd/Vc_max
    gamma = (gamma_no_dark+Kc*(1+pO2_mbar)*Rd/Vc_max)/denom
    return gamma


def CO2_compensation_no_dark(T_C,**kwargs):
    update_params()
    global case_params
    model_args = ['pO2_amb_mbar']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    pO2_mbar = kwargs['pO2_amb_mbar']
    Sco = selectivity_carbox_oxy(T_C,**kwargs)
    gamma = 0.5*Sco*pO2_mbar*10**-3
    return gamma


def selectivity_carbox_oxy(T_C,**kwargs):
    #source Galmes, 2016 [1]
    update_params()
    global case_params
    model_args = ['carbox_ox_sel_c','carbox_ox_sel_dHa_J_mol']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    c = kwargs['carbox_ox_sel_c']
    dHa = kwargs['carbox_ox_sel_dHa_J_mol']
    R = CONSTANTS['R_ig_J_K_mol']
    Sco = math.exp(c-dHa/(R*(T_C+273.15)))
    return Sco

def K_carbox(T_C,**kwargs):
    #source Galmes, 2016 [1]
    update_params()
    global case_params
    model_args = ['carbox_c','carbox_dHa_J_mol']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    c = kwargs['carbox_c']
    dHa = kwargs['carbox_dHa_J_mol']
    R = CONSTANTS['R_ig_J_K_mol']
    Kc = math.exp(c-dHa/(R*(T_C+273.15)))
    return Kc

def K_ox(T_C,**kwargs):
    #source Galmes, 2016 [1]
    update_params()
    global case_params
    model_args = ['ox_c','ox_dHa_J_mol']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    c = kwargs['ox_c']
    dHa = kwargs['ox_dHa_J_mol']
    R = CONSTANTS['R_ig_J_K_mol']
    Ko = math.exp(c-dHa/(R*(T_C+273.15)))
    return Ko

def k_carbox(T_C,**kwargs):
    #source FvCB 1980
    update_params()
    global case_params
    model_args = ['kc_Ha_J_mol','kc_k25C_s']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    k25C = kwargs['kc_k25C_s']
    dHa = kwargs['kc_Ha_J_mol']
    k_s = arrhenius(T_C,k25C,dHa)
    return k_s

def T_K(T_C):
    return T_C+273.15

def phi_carbox_oxy(T_C,pCO2_ubar,**kwargs):
    update_params()
    global case_params
    model_args = ['pO2_amb_mbar']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    pO2_mbar = kwargs['pO2_amb_mbar']
    Sco = selectivity_carbox_oxy(T_C,**kwargs)
    phi = pCO2_ubar/pO2_mbar*Sco*10**-3
    return phi


def arrhenius(T_C,k_ref,dHa,T_ref_C=25):
    HR_K = dHa/CONSTANTS['R_ig_J_K_mol']
    exp_term = HR_K*(1/T_K(T_ref_C)-1/T_K(T_C))
    k = k_ref*math.exp(exp_term)
    return k

"""sources
[1] Galmes, 2016 - A compendium of temperature responses of Rubisco kinetic traits: 
    variability among and within photosynthetic groups and impacts on photosynthesis modeling

"""