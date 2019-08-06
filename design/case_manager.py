import pandas as pd
import os
from design import climate as clm
from design import model as design
from utils.num_methods import monte_carlo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_TABLE = 'parameters'
SQL_OUTPUT = 'cases'
PARAM_XFILENAME = 'parameters.xlsx'
GROUPS = ['robot','conveyor','hvac','prices']
ptbl = None



WATCH_GROUP = 'kpi'
WATCH_FIELDS = ['capex','opex','revenue','capex_m2','simple_return']


def get_cases():
    clm.load()
    casetbl = pd.read_sql('select * from ' + SQL_OUTPUT,con=clm.engine)
    return casetbl

def run_mc(scope_groups=None,N_runs=500,refresh=True,threshold_conf=.8,conf_int=.9):
    clm.load()
    fun_handle =design.update
    output_fields = {WATCH_GROUP:WATCH_FIELDS}
    input_table=SQL_TABLE
    output_table=SQL_OUTPUT
    ctbl = monte_carlo(fun_handle=fun_handle,output_fields=output_fields,input_table=input_table,
                output_table=output_table,conf_int=conf_int,con=clm.engine,threshold_conf=threshold_conf,
                N_runs=N_runs,refresh=refresh,scope_groups=scope_groups)
    return ctbl


def import_parameters_from_excel():
    global ptbl,GROUPS, PARAM_XFILENAME
    clm.load()
    tbls = [pd.read_excel(os.path.join(BASE_DIR,PARAM_XFILENAME),grp)for grp in GROUPS]
    ptbl = pd.concat(tbls,axis=0)
    ptbl.to_sql(SQL_TABLE,con=clm.engine, if_exists='replace', index=False)


