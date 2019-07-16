import design.model as design
import fryield.model as plants


#design
#run the design module and reports overall kpis
design.update()

#use the design module to get x,y series to show the influence of plant spacing on yield, costs, and returns
plant_spacing_cm = [45,50,65,80]
kpi = []
for x in plant_spacing_cm:
    design.setup()
    case_params = design.case_params.copy()
    case_params['plants'].update({'plant_spacing_cm':x})
    kpi.append(design.update(case_params)['kpi'])
fryield = [x['yield_kg_m2_yr'] for x in kpi]
capex = [x['capex'] for x in kpi]
returns = [x['simple_return'] for x in kpi]


#plants
#run the plant module and reports yield and growth results
response = plants.update()

#use the plant module to get x,y series to show the influence of day light integral (dli) on yield
dli = [30.0,40.0,50.0,72.0]
fryield = [plants.update({'ps_dli':x})['yield_kg_m2_yr'] for x in dli]
