import pandas as pd
import numpy as np
import math as m

SUBGROUPS = ['prices','capex','opex']

robot_parameters = {'num_towers': 183,
                    'operation_hours': 18,
                    'trays_per_tower': 4,
                    'fruit_pl_d_day': .56,
                    'robot_rate': 20,
                    'indirect_fixed': 100,
                    'prices':{'electricity_kwh':0.18},
                    }

working_params = {}


def update(params=None):
    global SUBGROUPS
    setup()
    if params is not None:
        for p in params:
            if p in SUBGROUPS:
                for s in params[p]:
                    working_params[p][s] = params[p][s]
            working_params[p] = params[p]
    run()
    response = working_params.copy()
    response.update(result)
    return response


result = {'numR': 0,
          'numL': 0,
          'capex': {'total_USD': 0},
          'opex': {'total_USD': 0},
          }


def run():
    global result
    (numR, numL) = units_needed(working_params['num_towers'],
                                working_params['trays_per_tower'],
                                working_params['fruit_pl_d_day'],
                                working_params['operation_hours'],
                                working_params['robot_rate'])
    result.update({'numL': numL, 'numR': numR})
    result['capex']['total_USD'] = cap_cost(result['numR'], result['numL'])
    result['opex']['total_USD'] = op_cost(result['numR'],
                           result['numL'],
                           working_params['prices']['electricity_kwh'],
                           working_params['operation_hours'],
                           working_params['indirect_fixed'])


def setup():
    global working_params, robot_parameters
    working_params = robot_parameters


def run_cases(cases):
    for c in cases:
        for k in c:
            working_params[k] = c[k]
        update()
        c.update(result)


def units_needed(num_towers, trays_per_tower, fruit_plant_day, operation_hours, robot_rate):
    # robot fruit rate = fruits it can pick per hour
    fruits = num_towers*fruit_plant_day*12
    num_robots_needed = int(trays_per_tower*(m.ceil((
            float(fruits/(robot_rate*operation_hours))/trays_per_tower))))
    num_lights_needed = trays_per_tower*num_robots_needed
    return num_robots_needed, num_lights_needed


def cap_cost(num_robots, num_lights):
    arms_cost = 20000
    computer_cost = 2000
    scanner_cost = 1000
    stereovision_cost = 300
    lights1_cost = 10
    lights2_cost = 2.5
    robot_costs = [arms_cost, computer_cost, scanner_cost, stereovision_cost]
    cap_robot_parts = num_robots*sum(robot_costs)
    lights_costs = [lights1_cost, lights2_cost]
    cap_lights = num_lights*sum(lights_costs)
    total = cap_robot_parts + cap_lights
    return total


def op_cost(num_robots, num_lights, kw_price, operation_hours, indirect_fixed):
    indirect_fixed_total = num_robots*indirect_fixed
    arms_kw = .39
    computer_kw = .51
    scanner_kw = .0025
    stereovision_kw = .004
    lights1_kw = .005
    lights2_kw = .001
    lights_kw = num_lights*(lights1_kw + lights2_kw)
    robot_kw = num_robots*(arms_kw + computer_kw + scanner_kw + stereovision_kw)
    total_kw = lights_kw + robot_kw
    total = (total_kw*kw_price*operation_hours*365)+indirect_fixed_total
    return total




