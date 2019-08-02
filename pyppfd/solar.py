""" information adapted from Spitters 1986 solar radiation model

 article title :
    Separating the diffuse and direct component of global radiation
    and its implications for modeling a canopy photosynthesis part I
    components of incoming radiation

"""
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import os

spd = None
photons = None
rad_measures = ['extraterrestrial','global','direct and circumsolar']
SOLAR_CONSTANT = 1370 #W/m2 IEA 1978
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONSTANTS = {'Avogadro':6.023e+23,
             'Plank':6.626e-34,
             'speed_of_light': 3.0e+8,
             'PPFD_nm':[400,700],
             }

FILES = {'astm':os.path.join(BASE_DIR,'astm_g173_03.csv'),
}

default_params = {'angle_max':90,
                  'daylight_hrs':12,
                  'cloud_cover':0.25,
                  'ps_dli': 72,
                  }

case_params = {}


def setup():
    global case_params, default_parameters
    case_params = default_params.copy()


def update(params=None):
    setup()
    if params is not None:
        for p in params:
            case_params[p] = params[p]
    run()
    return case_params.copy()


def run():
    global case_params
    c = case_params.copy()
    daylight_hrs = c['daylight_hrs']
    angle_max = c['angle_max']
    cloud_cover = c['cloud_cover']
    ps_dli = day_light_integral(daylight_hpd=daylight_hrs,angle_max=angle_max,cloud_cover=cloud_cover)
    insolence_W_m2 = insolence_daily(daylight_hpd=daylight_hrs,angle_max=angle_max,cloud_cover=cloud_cover)

    case_params['ps_dli'] = ps_dli
    case_params['insolence_W_m2'] = insolence_W_m2


def day_light_integral(daylight_hpd=12,angle_max=90,cloud_cover=0.25,doy=90,resolution=100):
    #mol/m2/d
    global SOLAR_CONSTANT, photons
    load()
    nm = CONSTANTS['PPFD_nm']
    angles = [angle_max/90*0.5*math.pi*x/resolution for x in range(resolution+1)]
    ext = np.mean([extraterrestrial(a,doy) for a in angles])
    diff_r = diffuse_ratio(atm_transmission(cloud_cover))
    par_diff = par_csdiffuse(diff_r, angle_max*0.5/180*math.pi)
    diff_r = diff_r - par_diff
    global_rad = (1-diff_r)*ext
    photon_ratio = spectrum_photon_energy('direct and circumsolar',nm)
    dli = global_rad*photon_ratio*daylight_hpd*3600*10**-6
    return dli

def insolence_daily(daylight_hpd=12,angle_max=90,cloud_cover=0.25,doy=90,resolution=100):
    #W/m2
    global SOLAR_CONSTANT, photons
    load()
    angles = [angle_max/90*0.5*math.pi*x/resolution for x in range(resolution+1)]
    ext = np.mean([extraterrestrial(a,doy) for a in angles])
    diff_r = diffuse_ratio(atm_transmission(cloud_cover))
    global_rad = (1-diff_r)*ext
    insolence = global_rad*daylight_hpd/24
    return insolence


def photon_flux_by_hour(hour_of_day,daylight_hpd=12,angle_max=90,cloud_cover=0.25,doy=90):
    #umol/m2/s
    global SOLAR_CONSTANT, photons
    load()
    nm = CONSTANTS['PPFD_nm']
    angle = solar_angle_rad(hour_of_day,daylight_hpd,angle_max)
    ext = extraterrestrial(angle,doy)
    diff_r = diffuse_ratio(atm_transmission(cloud_cover))
    par_diff = par_csdiffuse(diff_r, angle*0.5/180*math.pi)
    diff_r = diff_r - par_diff
    global_rad = (1-diff_r)*ext
    photon_energy = spectrum_photon_energy('direct and circumsolar',nm)
    dli = global_rad*photon_energy
    return dli


def irradiation_by_hour(hour_of_day,daylight_hpd=12,angle_max=90,cloud_cover=0.25,doy=90):
    #W/m2
    global SOLAR_CONSTANT, photons
    load()
    angle = solar_angle_rad(hour_of_day,daylight_hpd,angle_max)
    ext = extraterrestrial(angle,doy)
    diff_r = diffuse_ratio(atm_transmission(cloud_cover))
    global_rad = (1-diff_r)*ext
    irradiation = global_rad
    return irradiation


def solar_angle_rad(hour_of_day,daylight_hpd=12,angle_max=90):
    intensity = 1 - math.fabs(2*(hour_of_day-12)/daylight_hpd)
    if intensity<0:
        intensity = 0
    angle = angle_max/90*0.5*math.pi*intensity
    return angle

def spectrum_photon_energy(rad_measure='global',nm=None):
    load()
    watts = spd[rad_measure].sum()
    if nm is None:
        pfd = photons[rad_measure].sum()*10**6
    else:
        pfd = photons.loc[nm[0]:nm[1]][rad_measure].sum()*10**6
    ratio = pfd/watts
    return ratio


def spectral_flux(nm,nm_1,spf,spf_1):
    nm_avg = 0.5*(nm+nm_1)
    spf_avg = 0.5*(spf+spf_1)
    ep = energy_photon(nm_avg)
    spf = (nm-nm_1)*spf_avg/ep
    return spf


def energy_photon(nm):
    global CONSTANTS
    lam = nm*1.0e-9
    N = CONSTANTS['Avogadro']
    h = CONSTANTS['Plank']
    c = CONSTANTS['speed_of_light']
    joules = N*h*c/lam
    return joules


def extraterrestrial(angle,doy):
    global SOLAR_CONSTANT
    ext = SOLAR_CONSTANT*(1+0.033*math.cos(2*math.pi*doy/365))*math.sin(angle)
    return ext


def par_csdiffuse(diff_ratio,angle):
    #Equation 10 adapted from Burtin 1981
    csdiffuse = circumsolar_diffuse(diff_ratio,angle)
    par_csd = (1+0.3*(1-diff_ratio**2))*csdiffuse
    return par_csd


def circumsolar_diffuse(diff_ratio,angle):
    #Equation 9 derived from Temps and Coulson 1977 and Klucher 1978
    cs_factor =(math.cos(0.5*math.pi-angle))**2*(math.cos(angle))**3
    diff_factor = 1-diff_ratio**2
    cs_diffuse = diff_ratio/(1+diff_factor*cs_factor)
    return cs_diffuse


def diffuse_ratio(atm_trans):
    #Equations (2a-d) De Bilt 1980
    if atm_trans<0.07:
        ratio = 1
    elif atm_trans<0.35:
        ratio = 1-2.3*(atm_trans-0.07)**2
    elif atm_trans<0.75:
        ratio = 1.33-1.46*atm_trans
    else:
        ratio = 0.23
    return ratio


def atm_transmission(cloud_cover):
    #Equation (12) Spitters 1986
    ratio = 0.2 + 0.56*(1-cloud_cover)
    return ratio


def set_photons():
    global photons, rad_measures
    photons = pd.DataFrame([],index=spd.index)
    photons['nm'] = spd.index
    photons['nm-1'] = photons['nm'].shift()
    for r in rad_measures:
        photons['r-1'] = spd[r].shift()
        photons['r'] = spd[r]
        photons[r] = photons.apply(lambda x:spectral_flux(x['nm'],x['nm-1'],x['r'],x['r-1']),axis=1)
        del photons['r'],photons['r-1']
    del photons['nm'], photons['nm-1']
    photons.drop(photons.index[0],inplace=True)


def load():
    global spd
    if spd is None:
        spd = pd.read_csv(FILES['astm'])
        spd.set_index('wavelength',inplace=True)
        set_photons()


def autorun():
    load()

if __name__ == "__main__":
    autorun()
