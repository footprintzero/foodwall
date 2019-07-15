import pandas as pd
import numpy as np
from food import nutrition as nut

feed = None
biogas = None
digestate = None

parameters = {}

def update(params):
    pass

def set_feed(diet='sgp',d=None):
    global feed
    if diet == 'sgp':
        d = nut.sgp_diet()
    feed = nut.get_waste(d)


