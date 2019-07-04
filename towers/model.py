import pandas as pd
import numpy as np
import math

pipe_IDs = {'0.5':1.6,'0.75':2,'1':25}
models = {'hueristic_friction_head':{'a':3,'v0':1.7,'hf0':2.3},
          'losses':{'nozzle':150,'height':25},
          }
tower = {'V_root_zone':8.65,
         'trays_per_tower':4,
         'void_fraction':0.3,
         'F_pipe_vol':0.1,
         'field_saturation':0.15
         }

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
    global tower
    if p is None:
        p = tower
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
