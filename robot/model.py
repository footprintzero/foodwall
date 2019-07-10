import pandas as pd
import numpy as np
import math as m

robot_parameters = {'num_towers': 183,
                    'operation_hours': 18,
                    'fruit_plant_day': .56,
                    'robot_rate': 20,
                    'kw_price': .18,
                    'indirect_fixed': 100}

working_params = {}


def update(params=None):
    setup()
    if params is not None:
        for p in params:
            working_params[p] = params[p]
    run()
    response = working_params.copy()
    response.update(result)
    return response


result = {'cap': 0,
          'op': 0,
          'numR': 0,
          'numL': 0,
          }


def run():
    global result
    (numR, numL) = units_needed(working_params['num_towers'],
                                working_params['fruit_plant_day'],
                                working_params['operation_hours'],
                                working_params['robot_rate'])
    result.update({'numL': numL, 'numR': numR})
    result['cap'] = cap_cost(result['numR'], result['numL'])
    result['op'] = op_cost(result['numR'],
                           result['numL'],
                           working_params['kw_price'],
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


def units_needed(num_towers, fruit_plant_day, operation_hours, robot_rate):
    # robot fruit rate = fruits it can pick per hour
    fruits = num_towers*fruit_plant_day*12
    num_robots_needed = int(4*(m.ceil((float(fruits/(robot_rate*operation_hours))/4))))
    num_lights_needed = 4*num_robots_needed
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







#hello world



