import pandas as pd

default_params = {'num_floors':1,
                  'building_floors':20,
                  'height_m':2.8,
                  'width_m':1.5,
                  'building_L':1.5,
                  'building_W':1.5,
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
    (L,W,w,h,Nfl,Blfl) = (case_params['building_L'], case_params['building_W'],
                 case_params['width_m'],case_params['height_m'],
                case_params['num_floors'],case_params['building_floors'])
    case_params['facade_L'] = Nfl*linear_length(L+0.5*w,W+0.5*w)
    case_params['building_GFA'] = building_GFA(L,W,Blfl)
    case_params['facade_GFA'] = facade_GFA(L,W,Nfl)
    case_params['facade_wall_area'] = facade_wall_area(L,W,h,w,Nfl)
    case_params['greenhouse_m3'] = greenhouse_m3(L,W,h,w,Nfl)


def greenhouse_m3(L, W,h,w,Nfl):
    w_max = facade_wall_area(L+w,W+w,h)
    w_min = facade_wall_area(L,W,h)
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