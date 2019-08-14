import pandas as pd
import os
from design import model as design
from design import database as db
from utils.num_methods import monte_carlo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_OUTPUT = 'cases'
PARAM_XFILENAME = 'parameters.xlsx'
GROUPS = ['prices','climate','plants','structure','tower','nutrients',
          'hvac','nursery','robot','conveyor','maintenance']
ptbl = None

WATCH_FIELDS = {'kpi':['capex','opex','revenue','profit','capex_m2','simple_return'],
                'capex':['structure','tower','robot','conveyor','hvac','nutrients','nursery'],
                'opex':['tower','robot','conveyor','hvac','nutrients','nursery','maintenance'],
                'revenue':['fruit','biogas']}

def get_cases():
    db.load()
    casetbl = pd.read_sql('select * from ' + SQL_OUTPUT,con=db.simeng)
    return casetbl


def run_mc(scope_groups=None,N_runs=500,refresh=True,threshold_conf=.8,conf_int=.9):
    global WATCH_FIELDS
    db.load()
    fun_handle =design.update
    input_table=db.PARAM_TABLE
    output_table=SQL_OUTPUT
    ctbl = monte_carlo(fun_handle=fun_handle,output_fields=WATCH_FIELDS,input_table=input_table,
                output_table=output_table,conf_int=conf_int,con=db.simeng,threshold_conf=threshold_conf,
                N_runs=N_runs,refresh=refresh,scope_groups=scope_groups)
    return ctbl


def import_parameters_from_excel():
    global ptbl,GROUPS, PARAM_XFILENAME
    db.load()
    tbls = [pd.read_excel(os.path.join(BASE_DIR,PARAM_XFILENAME),grp)for grp in GROUPS]
    ptbl = pd.concat(tbls,axis=0)
    ptbl.to_sql(db.PARAM_TABLE,con=db.simeng, if_exists='replace', index=False)


def grp_var(grp,field='simple_return',N_runs=20):
    ctbl = run_mc(scope_groups=[grp],N_runs=N_runs)
    values = ctbl[ctbl.parameter==field].value
    valid_cases = values[~pd.isnull(values)].copy()
    var = 0
    if len(valid_cases)>0:
        valmax = valid_cases.max()
        valmin = valid_cases.min()
        var = valmax-valmin
    return var

def get_cases(csv_export='cases.csv'):
    #query the table
    db.load()
    rawtbl = pd.read_sql('select * from cases', con=db.simeng)

    #assign group id
    caseid = list(rawtbl.caseid)
    caseid_nm = 0 ; groupid_j = 0
    groupid = []
    for c in caseid:
        if c < caseid_nm:
            groupid_j = groupid_j + 1
        caseid_nm = c
        groupid.append(groupid_j)
    rawtbl['groupid'] = groupid
    rawtbl['groupcaseid'] = [caseid[i] * 100 + groupid[i] for i in range(len(caseid))]
    if len(csv_export)>0:
        rawtbl.to_csv(csv_export,index=False)
    pvt = pd.pivot_table(rawtbl, index='groupcaseid',
                         values='value', columns='parameter', aggfunc='mean')

    return pvt

def get_case_slice(pvt,parameter,watch_fields=WATCH_FIELDS):
    slice = pvt[~pd.isnull(pvt[parameter])][watch_fields+[parameter]]
    return slice
