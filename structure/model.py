import pandas as pd
import math

default_params = {'num_floors':1,
                  'building_floors':20,
                  'height_m':2.8,
                  'width_m':1.5,
                  'building_L':1.5,
                  'building_W':1.5,
                  'wall_transmissivity':0.8,
                  'vbeam_spacing_m':1.6,
                  'beams_kg_m':10.61,
                  'panels_kg_m2':10.81,
                  'prices':{'beam_USD_kg':1.25,'PMMA_USD_kg':2.14,
                            'floor_USD_m2':13.19,'construction_factor':1.4375},
                  'capex':{'structure_USD':0,'beam_USD':0,'PMMA_USD':0,'floor_USD':0,
                           'materials_USD':0,'construction_USD':0},
                  }

case_params = {}


def setup():
    global case_params, default_parameters
    case_params = default_params


def update(params=None):
    setup()
    global case_params
    if params is not None:
        for p in params:
            case_params[p] = params[p]
    run()
    return case_params.copy()

def run():
    global case_params
    prices = case_params['prices']
    (L,W,w,h,vb_space,Nfl,Blfl) = (case_params['building_L'], case_params['building_W'],
                 case_params['width_m'],case_params['height_m'],case_params['vbeam_spacing_m'],
                case_params['num_floors'],case_params['building_floors'])

    beam_L = get_beam_length(L,W,h,w,vb_space)
    facade_GFA_m2 = facade_GFA(L,W,w,Nfl)

    case_params['facade_L'] = Nfl*linear_length(L+0.5*w,W+0.5*w)
    case_params['beam_L'] = beam_L
    case_params['building_GFA'] = building_GFA(L,W,Blfl)
    case_params['facade_GFA'] = facade_GFA_m2
    case_params['facade_wall_area'] = facade_wall_area(L,W,h,w,Nfl)
    case_params['greenhouse_m3'] = greenhouse_m3(L,W,h,w,Nfl)

    #capex
    capex = {}
    (beams_kg_m,panels_kg_m2,construction_factor) = (case_params['beams_kg_m'],
            case_params['panels_kg_m2'],prices['construction_factor'])

    panel_m2 = facade_GFA_m2 + case_params['facade_wall_area']

    capex['beam_USD'] = prices['beam_USD_kg']*beams_kg_m*beam_L
    capex['PMMA_USD'] = prices['PMMA_USD_kg']*panels_kg_m2*panel_m2
    capex['floor_USD'] = prices['floor_USD_m2']*facade_GFA_m2
    capex['materials_USD'] = sum([capex['beam_USD'],capex['PMMA_USD'],capex['floor_USD']])
    capex['construction_USD'] = capex['materials_USD']*construction_factor
    capex['structure_USD'] = capex['materials_USD']+capex['construction_USD']

    case_params['capex'] = capex

def get_beam_length(L,W,h,w,vb_space):
    interior_L = linear_length(L,W)
    exterior_L = linear_length(L+w,W+w)
    facade_L = 0.5*(interior_L+exterior_L)
    vbeam_L = 4*h*math.ceil(facade_L/vb_space)
    total_L = vbeam_L+2*(interior_L+exterior_L)
    return total_L

def greenhouse_m3(L, W,h,w,Nfl):
    w_max = linear_length(L+w,W+w)*h*Nfl
    w_min = linear_length(L,W)*h*Nfl
    m3 = 0.5*(w_max+w_min)*w*Nfl
    return m3

def facade_wall_area(L, W,h,w,Nfl):
    fl = linear_length(L+w,W+w)
    m2 = fl*h*Nfl
    return m2

def facade_GFA(L,W,w,Nfl):
    fl = linear_length(L+0.5*w,W+0.5*w)
    GFA = w*fl*Nfl
    return GFA


def linear_length(L,W):
    fl = 2*(L+W)
    return fl

def building_GFA(L,W,Blfl):
    GFA = L*W*Blfl
    return GFA