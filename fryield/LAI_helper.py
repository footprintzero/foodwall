from fryield import photosynthesis as ps
import pandas as pd
import numpy as np
from sklearn import linear_model

bins = [0.45,0.55,0.65,0.75,0.85,0.95]

params = {'Amin':0.05,'Amax':1,
          'Npts_A':50,'day_min':5,'day_max':365,
          'fit_intercept':False,
          'linear_model':{'alpha':-0.0930557677360452,'a0':0.1528484335022836},
}

def days_to_pct(LAI_pct,A):
    global params
    alpha = params['linear_model']['alpha']
    a0 = params['linear_model']['a0']
    a = a0+alpha*LAI_pct
    days = 1/(a*A)
    return days

def update_coeffs(**kwargs):
    global params, bins
    ps.setup()
    case = params.copy()
    if len(kwargs)>0:
        for k in kwargs:
            case[k] = kwargs[k]
    Amin = case['Amin'] ; Amax = case['Amax']
    day_min = case['day_min'] ; day_max = case['day_max']
    Npts_A = case['Npts_A'] ; fit_intercept = case['fit_intercept']
    bin_keys = [round(0.5*(bins[i]+bins[i+1]),1) for i in range(len(bins)-1)]
    A = [Amin + x*(Amax-Amin)/(Npts_A-1) for x in range(Npts_A)]
    days = [x for x in range(day_min,day_max)]
    cases = [(a,d) for a in A for d in days]

    pct = [ps.LAI_pct_max(x[1],ps_max_molCO2_m2_d=x[0]) for x in cases]

    df = pd.DataFrame({'pct':pct,'A':[x[0] for x in cases],'t':[x[1] for x in cases]})
    failed = df[df.pct==0].copy()
    success = df[df.pct!=0].copy()
    slices = success.groupby(pd.cut(success.pct,bins))
    regr = linear_model.LinearRegression(fit_intercept=fit_intercept)
    a = []
    for i in range(len(bins)-1):
        pct_key = bin_keys[i]
        test_set = slices.get_group(pd.Interval(bins[i],bins[i+1])).copy()
        test_set['invt'] = 1/test_set.t
        X = np.array(test_set.A).reshape(-1,1)
        y = np.array(test_set.invt).reshape(-1,1)
        regr.fit(X,y)
        a.append(regr.coef_[0][0])
    Xa = np.array(bin_keys).reshape(-1,1)
    ya = np.array(a).reshape(-1,1)
    regr = linear_model.LinearRegression(fit_intercept=True)
    regr.fit(Xa,ya)
    case['linear_model']['alpha'] = regr.coef_[0][0]
    case['linear_model']['a0'] = regr.intercept_[0]
    params = case

if __name__ == "__main__":
    update_coeffs()