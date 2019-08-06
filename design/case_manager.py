import pandas as pd
import os
from design import climate as clm
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARAM_XFILENAME = 'parameters.xlsx'
GROUPS = ['robot','conveyor','hvac','prices']
ptbl = None


def import_parameters_from_excel():
    global ptbl,GROUPS, PARAM_XFILENAME
    tbls = [pd.read_excel(os.path.join(BASE_DIR,PARAM_XFILENAME),grp)for grp in GROUPS]
    ptbl = pd.concat(tbls,axis=0)


