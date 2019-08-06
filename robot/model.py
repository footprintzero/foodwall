import pandas as pd
import numpy as np
import math as m

SUBGROUPS = ['prices','energy','capex','opex']

robot_parameters = {'num_towers': 186,
                    'op_hours': 18,
                    'trays_per_tower': 4,
                    'fruit_pl_d_day': .56,
                    'robot_rate': 20,
                    'indirect_fixed': 100,
                    'weeks_on':40,
                    'num_robots':4,
                    'num_lights':16,
                    'arms_kw':.39,
                    'computer_kw':.51,
                    'scanner_kw':.0025,
                    'stereo_kw':.004,
                    'lights1_kw':.005,
                    'lights2_kw':.001,
                    'prices':{'electricity_kwh':0.18,'arms_p':20000,'computer_p':2000,'scanner_p':1000,
                              'stereo_p':300,'lights1_p':10,'lights2_p':2.5},
                    'energy':{'total_kwh_year':20981},
                    'capex':{'total_usd':{93400}},
                    'opex':{'total_usd':{3776}}
                    }


wp = {}


def update(params=None):
    global SUBGROUPS, wp
    setup()
    if params is not None:
        for p in params:
            if p in SUBGROUPS:
                for s in params[p]:
                    wp[p][s] = params[p][s]
            else:
                wp[p] = params[p]
    run()
    return wp.copy()


def run():
    global wp
    prices=wp['prices']
    (numR, numL) = units_needed(wp['num_towers'],wp['trays_per_tower'],wp['fruit_pl_d_day'],
                                wp['op_hours'],wp['robot_rate'])
    wp['num_robots']=numR
    wp['num_lights']=numL
    cc = cap_cost(numR,numL,prices['arms_p'],prices['computer_p'],prices['scanner_p'],prices['stereo_p'],
                  prices['lights1_p'],prices['lights2_p'])
    wp['capex']['total_usd']=cc
    oc = op_cost(numR,numL,prices['electricity_kwh'],wp['op_hours'],wp['indirect_fixed'],
                 wp['arms_kw'],wp['computer_kw'],wp['scanner_kw'],wp['stereo_kw'],
                 wp['lights1_kw'],wp['lights2_kw'],wp['weeks_on'])
    wp['opex']['total_usd']=oc[0]
    wp['energy']['total_kwh_year']=oc[1]


def setup():
    global wp, robot_parameters
    wp = robot_parameters


def run_cases(cases):
    global report
    for c in cases:
        for k in c:
            wp[k] = c[k]
        update()
        c.update(wp)
    report = pd.DataFrame.from_records(cases)
    return report


def units_needed(num_towers=186, trays_per_tower=4, fruit_pl_d_day=.56, op_hours=18,
                 robot_rate=20):
    # robot fruit rate = fruits it can pick per hour
    fruits = num_towers*fruit_pl_d_day*trays_per_tower*3
    num_robots_needed = int(trays_per_tower*(m.ceil((
            float(fruits/(robot_rate*op_hours))/trays_per_tower))))
    num_lights_needed = trays_per_tower*num_robots_needed
    return num_robots_needed, num_lights_needed


def cap_cost(num_robots=4, num_lights=16, arms_p=20000,computer_p=2000,scanner_p=1000,
             stereo_p=300,lights1_p=10,lights2_p=2.5):
    robot_costs = [arms_p, computer_p, scanner_p, stereo_p]
    cap_robot_parts = num_robots*sum(robot_costs)
    lights_costs = [lights1_p, lights2_p]
    cap_lights = num_lights*sum(lights_costs)
    total = cap_robot_parts + cap_lights
    return total


def op_cost(num_robots=4, num_lights=16, kw_price=.18, op_hours=18, indirect_fixed=100,arms_kw=.39,
            computer_kw=.51,scanner_kw=.0025,stereo_kw=.004,lights1_kw=.005,lights2_kw=.001,
            weeks_on=40):
    indirect_fixed_total = num_robots*indirect_fixed
    lights_kw = num_lights*(lights1_kw + lights2_kw)
    robot_kw = num_robots*(arms_kw + computer_kw + scanner_kw + stereo_kw)
    total_kw = lights_kw + robot_kw
    total = (total_kw*kw_price*op_hours*weeks_on*7)+indirect_fixed_total
    kwh = total/kw_price
    return total,kwh







