import math
from scipy.integrate import solve_ivp
import pandas as pd
import scipy.stats as sct
import numpy as np

def monte_carlo(fun_handle,output_fields,input_table,output_table,con,threshold_conf=.8,conf_int=.9,
                N_runs=500,refresh=True,scope_groups=None):
    d90_factor = sct.norm.ppf(conf_int)*2
    output_grp = list(output_fields.keys())[0]

    def params_hash(params):
        hash = {}
        for grp in params:
            for k in params[grp]:
                if isinstance(params[grp][k],dict):
                    sub_params = {grp + '_' + k + '_' + z: params[grp][k][z] for z in params[grp][k]}
                    hash.update(sub_params)
                else:
                    pair = {grp+ '_' + k:params[grp][k]}
                    hash.update(pair)
        return hash

    def get_sample(mean,stdev,lbound,ubound):
        sample = np.random.normal(mean,stdev)
        if sample < lbound:
            sample = lbound
        elif sample > ubound:
            sample = ubound
        return sample

    def get_parameter_samples(maintbl):
        parameters = maintbl.parameter.unique()
        pmin = [maintbl[maintbl.parameter == p]['min'].iloc[0] for p in parameters]
        pmax = [maintbl[maintbl.parameter == p]['max'].iloc[0] for p in parameters]
        p_mean = [.5 * (pmax[i] + pmin[i]) for i in range(len(parameters))]
        stdev = [(pmax[i] - pmin[i]) * .5 / d90_factor for i in range(len(parameters))]
        sample = [get_sample(p_mean[i], stdev[i], pmin[i], pmax[i]) for i in range(len(parameters))]
        grp_params = dict(zip(parameters, sample))
        return grp_params
    def get_case():
        ptbl = pd.read_sql('select * from ' + input_table,con=con)
        ptbl = ptbl[ptbl.confidence<threshold_conf].copy()
        if scope_groups is None:
            groups = ptbl.group.unique()
        else:
            groups = scope_groups
        params={}
        for grp in groups:
            grp_params = {}
            grptbl = ptbl[ptbl.group==grp].copy()
            maintbl = grptbl[pd.isnull(grptbl.subgroup)].copy()
            if len(maintbl)>0:
                grp_params = get_parameter_samples(maintbl)

            subgrouptbl = grptbl[~pd.isnull(grptbl.subgroup)].copy()
            if len(subgrouptbl)>0:
                subgroups = list(subgrouptbl.subgroup.unique())
                for sgrp in subgroups:
                    sgrp_params = get_parameter_samples(subgrouptbl[subgrouptbl.subgroup==sgrp])
                    grp_params[sgrp] = sgrp_params
            params[grp] = grp_params

        try:
            all_case = fun_handle(params)
            case = {fld: all_case[output_grp][fld] for fld in output_fields[output_grp]}
        except BaseException as e:
            case = {fld: np.nan for fld in output_fields[output_grp]}

        case.update(params_hash(params))
        return case
    #ctbls = []
    for n in range(N_runs):
        case=get_case()
        values = list(case.values())
        fields = list(case.keys())
        caseid = [n for x in range(len(values))]
        ctbl = pd.DataFrame({'caseid':caseid,'parameter':fields,'value':values})
        if n==0 and refresh:
            action = 'replace'
        else:
            action = 'append'
        #ctbls.append(ctbl)
        ctbl.to_sql(output_table,if_exists=action,con=con,index=False)
    #return pd.concat(ctbls,axis=0)





def newton(fun_handle,y,x0,params={},hfull=1,dh=0.001,tolerance=0.001,maxiter=100,
           ymax=None,ymin=None,xrange=None):
    def y_at_x(x,dh):
        ym = fun_handle(x - 0.5 * dh, params)
        yp = fun_handle(x + 0.5 * dh, params)
        y0 = 0.5 * (yp + ym)
        e0 = 0.5 * (yp + ym-2*y)
        e = math.fabs(e0)
        dydx = (yp - ym) / dh
        return (y0,ym,yp,e0,e,dydx)
    e = 100 ; i = 0
    x = x0 ; dydx = 1
    h = hfull
    while (e>tolerance) and (i<maxiter):
        (y0,ym,yp,e0,e,dydx) = y_at_x(x,dh)
        if dydx==0:
            dh = 10*dh
        else:
            h = hfull
            step = h *e0 / dydx
            xt = x - step
            (y0, ym, yp, e0, e, dydx) = y_at_x(xt, dh)
            if not ((ymin is None) and (ymax is None)):
                a = 0
                if ymin is None: #only ymax
                    stop_condition = ((ym > ymax) or (yp > ymax))
                elif ymax is None: #only ymin
                    stop_condition = ((ym < ymin) or (yp < ymin))
                else: #both
                    stop_max = ((ym > ymax) or (yp > ymax))
                    stop_min = ((ym < ymin) or (yp < ymin))
                    stop_condition = (stop_min and stop_max)
                while (stop_condition and (a<maxiter)):
                    h = 0.5*h
                    step = h * e0 / dydx
                    xt = x - step
                    (y0, ym, yp, e0, e, dydx) = y_at_x(xt, dh)
                    a = a + 1
            x = xt
        i = i+1
    return (x,e,i)

"""
scipy.integrate.solve_ivp(fun, t_span, y0, method='RK45', 
    t_eval=None, dense_output=False, events=None, vectorized=False, **options)

fun :
    Right-hand side of the system. The calling signature is fun(t, y). 
    Here t is a scalar, and there are two options for the ndarray y: 
    It can either have shape (n,); then fun must return array_like with shape (n,). 
    Alternatively it can have shape (n, k); 
    then fun must return an array_like with shape (n, k), 
    i.e. each column corresponds to a single column in y. 
    The choice between the two options is determined by vectorized argument (see below).

"""

def rk45_integrate1D(dydt,tmin,tmax,y0):
    result = solve_ivp(dydt,[tmin,tmax],[y0])
    return result.y[0][-1]

def quadratic_roots(a,b,c):
    x_m = math.nan ; x_p = math.nan
    if ((b==0) and (c/a<0)):
        x_m = math.sqrt(-1*c/a)
        x_p = x_m
    else:
        radical = b**2-4*a*c
        if radical >=0:
            x_m = 0.5*1/a *( -b - math.sqrt(radical))
            x_p = 0.5*1/a *( -b + math.sqrt(radical))
    return (x_m,x_p)

