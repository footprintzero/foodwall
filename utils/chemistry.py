import math
MOL_W = {'C':12.01,'H':1.01,'O':15.99,'N':14.0,'S':32.0}

def mol_W(formula):
    MW = 0
    letters = [x for x in formula if not x.isdigit()]
    multiple = dict(zip(letters,[int(x) for x in formula if x.isdigit()]))
    if len(letters)>0:
        for l in letters:
            MW_i = MOL_W[l]
            MW+= MW_i*multiple[l]
    return MW

def T_K(T_C):
    return T_C+273.15

def antoine_psat(T_C,A=5.40221,B=1838.675,C=-31.737):
    exp_term = A - B / (T_K(T_C)+ C)
    return math.exp(exp_term)