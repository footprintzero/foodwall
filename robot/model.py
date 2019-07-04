import pandas as pd
import numpy as np
import math as m

robot_parameters = {'num_robots': 4,
                    'num_lights': 16,
                    'num_towers': 183,
                    'operation_hours': 18,
                    'fruit_plant_day': .56,
                    'robot_cycle_time': 3,
                    'kw_price': .18}

working_params = {}


def update(params=None):
    setup()
    if params is not None:
        for p in params:
            working_params[p] = params[p]
    run()


result = {'cap',
          'op',
          'numR',
          'numL'}


def run():
    global result
    result['cap'] = cap_cost(working_params['num_robots', 'num_lights'])
    result['op'] = op_cost(working_params['num_robots', 'num_lights', 'kw_price', 'operation_hours'])
    result['numR', 'numL'] = units_needed(working_params['num_towers', 'fruit_plant_day', 'operation_hours',
                                                         'robot_cycle_time'])


def setup():
    global working_params, robot_parameters
    working_params = robot_parameters


results_dictionary ={}
def results():
    run()
    global results_dictionary
    results_dictionary.pd.append(result)

def units_needed(num_towers, fruit_plant_day, operation_hours, robot_cycle_time):
    # robot cycle time is how many minutes to pick one fruit
    robot_cycle_time2 = robot_cycle_time/60
    fruit_hour = num_towers*fruit_plant_day*(12/operation_hours)
    num_robots_needed = m.ceil(fruit_hour*robot_cycle_time2)
    num_lights_needed = 4*num_robots_needed
    return num_robots_needed, num_lights_needed


def cap_cost(num_robots,num_lights):
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


def op_cost(num_robots, num_lights, kw_price, operation_hours):
    arms_kw = .39
    computer_kw = .51
    scanner_kw = .0025
    stereovision_kw = .004
    lights1_kw = .005
    lights2_kw = .001
    lights_kw = num_lights*[lights1_kw, lights2_kw]
    robot_kw = num_robots*[arms_kw, computer_kw, scanner_kw, stereovision_kw]
    total_kw = sum(lights_kw) + sum(robot_kw)
    total = total_kw*kw_price*operation_hours*365
    return total




