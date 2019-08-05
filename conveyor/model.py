import pandas as pd
import math as m

SUBGROUPS = ['prices','energy','capex','opex']

conveyor_params={
    'num_towers': 185,
    'building_l': 150,
    'building_w': 15,
    'rpd': 20,  # rotations per day
    'lub_amount': 3,
    'floors': 1,
    'op_hours': 18,
    'd_pull_c': 750,  # driver pull capacity in pounds
    'cw_lb_ft': 3.3,  # chain weight (pounds per foot)
    'systemw': 1.5,
    'lub_rate': .00000606,  # gallons of lubricant per meter of conveyor movement
    'driver_kw': 1.11855,  # kw determined from hp of given motor
    'driver_max_speed': .2286,  #m/s
    'lubricant':72,
    'tower_lbs':150,
    'pendant_lbs':2,
    'weeks_on':40,
    'kw_price':.18,
    'prices':{'track': 44.5,'welding_jig': 123,'brackets': 90,'inspector': 313,'curves': 195,
              'driver': 8527,'chain': 30.9,'lubricator': 4768,'pendants': 53,},
    'energy':{'total_kwh_year': 5100},
    'capex':{'total_usd': 127830},
    'opex':{'total_usd': 1742,'lubricant_op': 920,'driver_op': 821},


}

wp={}

def setup():
    global wp
    global conveyor_params
    wp = conveyor_params


def update(params=None):
    setup()
    if params is not None:
        for p in params:
            wp[p] = params[p]
    run()
    return wp.copy()


def run():
    global wp
    cc = cap_costs(wp,num_towers=wp['num_towers'],building_l=wp['building_l'],building_w=wp['building_w'],
                   tower_lbs=wp['tower_lbs'],pendant_lbs=wp['pendant_lbs'],floors=wp['floors'],
                   d_pull_c=wp['d_pull_c'],cw_lb_ft=wp['cw_lb_ft'],systemw=wp['systemw'])
    oc = op_costs(driver_kw=wp['driver_kw'],driver_max_speed=wp['driver_max_speed'],op_hours=wp['op_hours'],
                  building_l=wp['building_l'],building_w=wp['building_w'],systemw=wp['systemw'],
                  rpd=wp['rpd'],weeks_on=wp['weeks_on'],kw_price=wp['kw_price'],lubricant=wp['lubricant'],
                  lub_rate=wp['lub_rate'],floors=wp['floors'],num_towers=wp['num_towers'],
                  tower_lbs=wp['tower_lbs'],pendant_lbs=wp['pendant_lbs'],d_pull_c=wp['d_pull_c'],
                  cw_lb_ft=wp['cw_lb_ft'])
    wp['energy']['total_kwh_year']= oc[3]
    wp['opex']['total_usd']=oc[0]
    wp['opex']['lubricant_op']=oc[2]
    wp['opex']['driver_op']=oc[1]
    wp['capex']['total_usd']=cc[0]

def num_units(num_towers=186,building_l=150,building_w=15,tower_lbs=150,pendant_lbs=2,
              floors=1,d_pull_c=750,cw_lb_ft=3.3,systemw=1.5):
    r=.5*systemw
    ll_curves = 4 * curve_ll(90, r) * 3.28084
    ll_ft = ll_curves+(3.28084*2*(building_l+building_w))
    num_wj = 1
    num_brackets = (m.ceil(ll_ft/10))
    num_inspector = 1
    num_driver= m.ceil(.025*((ll_ft*cw_lb_ft)+(num_towers*(tower_lbs+pendant_lbs)))/d_pull_c)
    num_lubricator = 1
    num_pendants = num_towers
    units = [ll_ft,num_wj,num_brackets,num_inspector,ll_curves,num_driver,ll_ft,num_lubricator,num_pendants]
    num_units = [u*floors for u in units]
    return num_units


def curve_ll(angle,radius):
    ll = 2*(angle/360)*m.pi*radius
    return ll


def cap_costs(params,**kwargs):
    nu = num_units(**kwargs)
    prices = params['prices'].copy()
    prices_l = [p for p in prices.values()]
    costs = [n*p for n, p in zip(nu, prices_l)]
    total = sum(costs)
    costs.insert(0, total)
    return costs


def op_costs(driver_kw=1.11855,driver_max_speed=.2286,op_hours=18,building_l=150,building_w=15,systemw=1.5,
             rpd=20,weeks_on=40,kw_price=.18,lubricant=72,lub_rate=.00000606,floors=1,**kwargs):
    num_driver = num_units(building_l=building_l,building_w=building_w,floors=floors,systemw=systemw,**kwargs)[5]
    length = 2*(building_l+building_w+(2*systemw))
    d_avg_s = rpd*(length/op_hours/3600)
    driver_op = (d_avg_s/driver_max_speed)*driver_kw*18*7*weeks_on*num_driver*kw_price
    driver_energy = driver_op/kw_price
    rotations=rpd*length*7*weeks_on
    lub_op = rotations*lub_rate*lubricant*floors
    total_op = driver_op+lub_op
    return [total_op,driver_op,lub_op,driver_energy]

