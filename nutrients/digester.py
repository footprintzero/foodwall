import pandas as pd
import numpy as np
from food import nutrition as nut

streams = {'feed':{},
           'biogas':{},
           'digestate':{},
           'aerobic_effluent':{},
           }

feed = None
biogas = {}
digestate = {}

parameters = {}

class Stream(object):
    def __init__(self,diet):
        comp_dry = diet.elements()/diet.wt_g('dry')
        self.CHONS = [comp_dry[x] for x in ['C','H','O','N','S']]
        self.water_pct = diet.elements()/diet.wt_g('wet')
        self.kg_wet = diet.wt_g('wet')/1000
        self.kg_dry = diet.wt_g('dry')/1000
    def stoichiometric_biogas_yields_kg(self):
        x = self.CHONS
        MW = [12.0,1.01,16.0,14.0,32.0]
        yields = stoichiometric_biogas_yield_kg(
            x[0]/MW[0],x[1]/MW[1],x[2]/MW[2],x[3]/MW[3],x[4]/MW[4])
        yields_kg = [yields[c]*self.kg_dry for c in yields]
        return yields_kg

def update(params):
    pass

def set_feed(diet='sgp',d=None):
    global feed
    if diet == 'sgp':
        d = nut.sgp_diet()
    feed = nut.get_waste(d)

def stoichiometric_biogas_yield_kg(C,H,O,N,S):
    yields = {'CH4':0,'CO2':0,
              'NH3':0,'H2S':0}
    MW = [12.0+16.0*2,14.0+1.01*3,1.01*2+32.0,1.01*4+12]
    yields['CO2'] = C*MW[0] ; yields['NH3'] = N*MW[1]
    yields['H2S'] = S*MW[2]
    yields['CH4'] = (C+0.25*H-0.5*O-0.75*N-0.5*S)*MW[3]
    return yields


