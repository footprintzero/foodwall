import design.model as design
import pyppfd.solar as light
import towers.model as tower
import fryield.model as plants
import hvac.model as hvac
from utils.num_methods import newton

#design
#run the design module for default parameters and reports overall kpis
design.update()

#use the design module to get x,y series to show the influence of plant spacing on yield, costs, and returns
#this naive model does not account for plant yield drop due to over-crowding
plant_spacing_cm = [45,50,65,80]
kpi = [design.update({'tower':{'plant_spacing_cm':x}})['kpi'] for x in plant_spacing_cm]
fryield = [x['yield_kg_m2_yr'] for x in kpi]
capex = [x['capex'] for x in kpi]
returns = [x['simple_return'] for x in kpi]

#light
#run the light model for different cases of daylight hrs, max sun angle (proxy for latitute) and cloud cover
latitudes = [(45,6,0.1),(75,8,0.1),(90,10,0.5),(90,10,0)]
photons_m2_d = [light.day_light_integral(daylight_hpd=x[1],angle_max=x[0],cloud_cover=x[2]) for x in latitudes]
watts_m2 = [light.insolence_daily(daylight_hpd=x[1],angle_max=x[0],cloud_cover=x[2]) for x in latitudes]


#towers
#run the towers model for different cases of plant spacing and floor height
floor_heights = [2,2.8,4,8]
tower_cases = [(s,h) for s in plant_spacing_cm for h in floor_heights]
tresponses = [tower.update({'plant_spacing_cm':c[0],'height_m':c[1]}) for c in tower_cases]
num_towers = [r['num_towers'] for r in tresponses]
num_plants = [r['num_plants'] for r in tresponses]
total_USD = [r['capex']['towers_USD'] for r in tresponses]
USD_per_tower = [total_USD[i]/num_towers[i] for i in range(len(tower_cases))]
USD_per_plant = [total_USD[i]/num_plants[i] for i in range(len(tower_cases))]


#plants
#run the plant module for default settings and reports yield and growth results
response = plants.update()

#use the plant module to get x,y series to show the influence of day light integral (dli) on yield
fryield = [plants.update({'ps_dli':x})['yield_kg_m2_yr'] for x in photons_m2_d]

#hvac
Fguess = 20000
params = {'t_rate':0.0006,'insolence':0.25047,'rf':0.1,
          'i_temp':300.15,'i_humidity':0.65,'a_temp':305.15,
          'a_humidity':0.7,'f_hvac_cfm':15000,'f_nv_cfm':0,'num_towers':185,
          'p_towers':12,'wall_a':957.6,'roof_a':504,'u':3,'daytime':True,'interest':0}
hum = [0.75, 0.8, 0.9, 0.95]
hmax = 1; hfull = 0.25 ; dh = 1000
F = [newton(hvac.hvac_wrapper_humidity,h,Fguess,params,dh=dh,ymax=hmax,hfull=hfull)[0] for h in hum]
