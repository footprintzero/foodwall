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
