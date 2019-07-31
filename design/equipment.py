import math
STD_PROCESS_EQ = ['tank','vessel','mixer','furnace','dosing','pump','blower']
models = {'hueristic_friction_head':{'a':3,'v0':1.7,'hf0':2.3},
          'losses':{'nozzle':150,'height':25},
          }
COSTMODEL_ARGS = {'tank':{'wall_matl_USD_m2':45,
                          'thickness_scale_exp':0.85,
                          'cost_model':'surface_area',
                          'electricity_kwh':0.18,
                          },
                  'mixer': {
                          'electricity_kwh':0.18,
                          'cost_slope_USD_kW': 150,
                          'cost_int_USD': 2000,
                            },
                  'pump': {
                      'electricity_kwh': 0.18,
                      'cost_slope_USD_kW': 20,
                      'cost_int_USD': 150,
                  },
                  'blower': {
                      'electricity_kwh': 0.18,
                      'cost_slope_USD_kW': 20,
                      'cost_int_USD': 150,
                  },
                  }
CONSTANTS = {'hrs_per_day':24}
DIM_ARGS = {'tank':{'height_m':2.5,
                    'fluid_density_kg_m3':1000,
                    'LD':2,
                    'sizing_model':'fixed_height',
                    },
            'mixer': {
                'sizing_model': 'LP_mixing',
                'V_m3':25,
                'LP_mixing_factor_kW_m3': 0.1,
                'HP_blending_factor_kJ_kg': 30,
                'HP_blending_hpd': 0.5,
            },
            'pump': {
                'sizing_model': 'pump',
                'loading_kgph':17.25,
                'fluid_density_kg_m3': 1000,
                'head_kPa': 200.0,
                'operation_hpd': 24.0,
                'energy_MAX_kW': 10.0,
                'energy_AVG_kW': 10.0,
            },
            'blower': {
                'sizing_model': 'blower',
                'loading_kgph':17.25,
                'fluid_density_kg_m3': 1.255,
                'friction_factor': 0.1,
                'head_kPa': 200.0,
                'velocity_m_s': 2.0,
                'operating_hpd': 24.0,
                'energy_MAX_kW': 10.0,
                'energy_AVG_kW': 10.0,
            },
            }

def cylinder_surface_area_m2(D_m, height_m):
    SA_m2 =math.pi*(0.5*D_m**2+D_m*height_m)
    return SA_m2

class Asset(object):
    capex = 0
    opex = 0
    def __init__(self,capex,opex):
        self.capex=capex
        self.opex=opex

    def __add__(self,other):
        capex = self.capex+other.capex
        opex = self.opex+other.opex
        ass = Asset(capex,opex)
        return ass

    def __radd__(self,other):
        if other == 0:
            return self
        else:
            return self.__add__(other)


class Equipment(Asset):
    name = ''
    eqp_type=''
    dimensions = {}
    costs_model = {}
    components = {}
    load_size = 0
    load_basis = ''
    rate_kgph = 0
    energy_kW = 0
    electricity_kwh = 0.18
    consumables = 0
    has_dimensions = False
    has_capex = False
    has_opex = False
    def __init__(self,load_size,load_basis='kgph',name='',eqp_type='tank',**kwargs):
        self.load_size = load_size
        self.load_basis = load_basis
        self.name = name
        self.eqp_type = eqp_type
        self.set_defaults()
        if 'electricity_kwh' in kwargs:
            self.electricity_kwh=kwargs['electricity_kwh']
        if self.eqp_type in COSTMODEL_ARGS:
            for ar in [x for x in kwargs if x in COSTMODEL_ARGS[self.eqp_type]]:
                self.costs_model[ar] =kwargs[ar]
        if self.eqp_type in DIM_ARGS:
            for ar in [x for x in kwargs if x in DIM_ARGS[self.eqp_type]]:
                self.dimensions[ar] =kwargs[ar]
        self.size()
        capex=self.get_capex()
        opex=self.get_opex()
        super(Equipment,self).__init__(capex,opex)

    def set_defaults(self):
        if self.has_components():
            for c in self.components:
                self.components[c].set_defaults()

    def has_components(self):
        return len(self.components)>0

    def size(self):
        if self.has_components():
            for c in self.components:
                self.components[c].size()

    def get_energy(self):
        if self.has_components():
            comp_energy = 0
            for c in self.components:
                comp_energy+=self.components[c].get_energy()
            self.energy_kW +=comp_energy
        return self.energy_kW

    def get_capex(self):
        capex = 0
        if self.has_components():
            comp_capex = 0
            for c in self.components:
                comp_capex+=self.components[c].get_capex()
            capex += comp_capex
        return capex

    def get_opex(self):
        opex=  0
        if self.has_components():
            comp_opex = 0
            for c in self.components:
                comp_opex+=self.components[c].get_opex()
            opex += comp_opex
        return opex


class TankEqp(Equipment):
    V_m3 = 0
    load_rate_kgph = 0
    turnover_days = 1
    def __init__(self,load_rate_kgph,turnover_days,**kwargs):
        eqp_type = 'tank'
        kwargs['eqp_type'] = eqp_type
        self.load_rate_kgph = load_rate_kgph
        self.turnover_days = turnover_days
        super(TankEqp,self).__init__(load_rate_kgph,load_basis='kgph',**kwargs)

    def set_defaults(self):
        self.dimensions = DIM_ARGS[self.eqp_type].copy()
        self.costs_model = COSTMODEL_ARGS[self.eqp_type].copy()
        if self.has_components():
            for c in self.components:
                self.components[c].set_defaults()

    def size(self):
        if ~self.has_dimensions:
            fluid_density_kg_m3 = self.dimensions['fluid_density_kg_m3']
            self.V_m3 = self.load_rate_kgph/fluid_density_kg_m3*CONSTANTS['hrs_per_day']*self.turnover_days
            if self.dimensions['sizing_model'] == 'fixed_height':
                height_m = self.dimensions['height_m']
                D_m = math.sqrt(4*self.V_m3*1/math.pi*1/height_m)
                self.dimensions['D_m'] = D_m
            self.dimensions['SA_m2'] = cylinder_surface_area_m2(D_m,height_m)
            self.dimensions['LD'] = height_m/D_m
            if self.has_components():
                for c in self.components:
                    self.components[c].size()
            self.has_dimensions=True

    def get_capex(self):
        capex=0
        self.size()
        if ~self.has_capex:
            if self.costs_model['cost_model'] == 'surface_area':
                wall_matl_USD_m2 = self.costs_model['wall_matl_USD_m2']
                th_scale_exp = self.costs_model['thickness_scale_exp']
                th_scale_factor = (1+0.001*(self.V_m3*1000)**th_scale_exp)
                capex = self.dimensions['SA_m2']*th_scale_factor*wall_matl_USD_m2
            if self.has_components():
                comp_capex = 0
                for c in self.components:
                    comp_capex += self.components[c].get_capex()
                capex += comp_capex
            self.has_capex=True
        return capex

class MixerEqp(Equipment):
    load_rate_kgph = 0
    energy_kW = 0
    def __init__(self,load_rate_kgph,**kwargs):
        eqp_type = 'mixer'
        kwargs['eqp_type'] = eqp_type
        self.load_rate_kgph = load_rate_kgph
        super(MixerEqp,self).__init__(load_rate_kgph,load_basis='kgph',**kwargs)

    def set_defaults(self):
        self.dimensions = DIM_ARGS[self.eqp_type].copy()
        self.costs_model = COSTMODEL_ARGS[self.eqp_type].copy()
        if self.has_components():
            for c in self.components:
                self.components[c].set_defaults()

    def size(self):
        if ~self.has_dimensions:
            energy_kW = 0
            model = self.dimensions['sizing_model']
            if model == 'LP_mixing':
                V_m3 = self.dimensions['V_m3']
                energy_kW = self.dimensions['LP_mixing_factor_kW_m3']*V_m3
            elif model =='HP_blending':
                energy_kW = self.dimensions['HP_blending_factor_kJ_kg']*self.load_rate_kgph/3600
            if self.has_components():
                for c in self.components:
                    self.components[c].size()
                    energy_kW +=self.components[c].energy_kW
            self.energy_kW = energy_kW
            self.has_dimensions=True


    def get_capex(self):
        capex=0
        self.size()
        if ~self.has_capex:
            a = self.costs_model['cost_slope_USD_kW']
            b = self.costs_model['cost_int_USD']
            capex = a*self.energy_kW + b
            if self.has_components():
                comp_capex = 0
                for c in self.components:
                    comp_capex += self.components[c].get_capex()
                capex += comp_capex
            self.has_capex=True
        return capex

    def get_opex(self):
        opex=0
        self.size()
        if ~self.has_opex:
            #energy kW
            opex = electricity_cost_USD_yr(self.energy_kW,self.electricity_kwh)
            if self.has_components():
                comp_opex = 0
                for c in self.components:
                    comp_opex += self.components[c].get_opex()
                opex += comp_opex
            self.has_opex=True
        return opex

class PumpEqp(Equipment):
    load_rate_kgph = 0
    head_kPa = 200.0
    energy_kW = 0
    energy_MAX_kW = 0
    def __init__(self,load_rate_kgph,head_kPa,**kwargs):
        eqp_type = 'pump'
        kwargs['eqp_type'] = eqp_type
        self.load_rate_kgph = load_rate_kgph
        self.head_kPa = head_kPa
        super(PumpEqp,self).__init__(load_rate_kgph,load_basis='kgph',**kwargs)

    def set_defaults(self):
        self.dimensions = DIM_ARGS[self.eqp_type].copy()
        self.costs_model = COSTMODEL_ARGS[self.eqp_type].copy()
        if self.has_components():
            for c in self.components:
                self.components[c].set_defaults()

    def size(self):
        if ~self.has_dimensions:
            energy_kW = 0 ; energy_MAX_kW = 0
            model = self.dimensions['sizing_model']
            operation_hpd = self.dimensions['operation_hpd']
            density_kg_m3 = self.dimensions['fluid_density_kg_m3']
            load_rate_LPH = self.load_rate_kgph/density_kg_m3*1000
            energy_kW = self.head_power_kW(self.head_kPa,load_rate_LPH)
            if operation_hpd<24.0:
                instantaneous_LPH = 24/operation_hpd
                energy_MAX_kW = self.head_power_kW(self.head_kPa, instantaneous_LPH)
            else:
                energy_MAX_kW = self.energy_kW
            if self.has_components():
                for c in self.components:
                    self.components[c].size()
                    energy_kW +=self.components[c].energy_kW
                    if hasattr(self.components[c],'energy_MAX_kW'):
                        energy_MAX_kW += self.components[c].energy_MAX_kW
            self.energy_kW = energy_kW
            self.energy_MAX_kW = energy_MAX_kW
            self.has_dimensions=True


    def get_capex(self):
        capex=0
        self.size()
        if ~self.has_capex:
            a = self.costs_model['cost_slope_USD_kW']
            b = self.costs_model['cost_int_USD']
            capex = a*self.energy_MAX_kW + b
            if self.has_components():
                comp_capex = 0
                for c in self.components:
                    comp_capex += self.components[c].get_capex()
                capex += comp_capex
            self.has_capex=True
        return capex

    def get_opex(self):
        opex=0
        self.size()
        if ~self.has_opex:
            #energy kW
            opex = electricity_cost_USD_yr(self.energy_kW,self.electricity_kwh)
            if self.has_components():
                comp_opex = 0
                for c in self.components:
                    comp_opex += self.components[c].get_opex()
                opex += comp_opex
            self.has_opex=True
        return opex

    def head_power_kW(self,H_kPa,Q_LPH):
        kW = H_kPa*Q_LPH*1/3600*1/1000
        return kW


class BlowerEqp(Equipment):
    load_rate_kgph = 0
    head_kPa = 200.0
    energy_kW = 0
    energy_MAX_kW = 0
    def __init__(self,load_rate_kgph,head_kPa,**kwargs):
        eqp_type = 'blower'
        kwargs['eqp_type'] = eqp_type
        self.load_rate_kgph = load_rate_kgph
        self.head_kPa = head_kPa
        super(BlowerEqp,self).__init__(load_rate_kgph,load_basis='kgph',**kwargs)

    def set_defaults(self):
        self.dimensions = DIM_ARGS[self.eqp_type].copy()
        self.costs_model = COSTMODEL_ARGS[self.eqp_type].copy()
        if self.has_components():
            for c in self.components:
                self.components[c].set_defaults()

    def size(self):
        if ~self.has_dimensions:
            energy_kW = 0 ; energy_MAX_kW = 0
            model = self.dimensions['sizing_model']
            operation_hpd = self.dimensions['operation_hpd']
            density_kg_m3 = self.dimensions['fluid_density_kg_m3']
            load_rate_LPH = self.load_rate_kgph/density_kg_m3*1000
            energy_kW = self.head_power_kW(self.head_kPa,load_rate_LPH)
            if operation_hpd<24.0:
                instantaneous_LPH = 24/operation_hpd
                energy_MAX_kW = self.head_power_kW(self.head_kPa, instantaneous_LPH)
            else:
                energy_MAX_kW = self.energy_kW
            if self.has_components():
                for c in self.components:
                    self.components[c].size()
                    energy_kW +=self.components[c].energy_kW
                    if hasattr(self.components[c],'energy_MAX_kW'):
                        energy_MAX_kW += self.components[c].energy_MAX_kW
            self.energy_kW = energy_kW
            self.energy_MAX_kW = energy_MAX_kW
            self.has_dimensions=True


    def get_capex(self):
        capex=0
        self.size()
        if ~self.has_capex:
            a = self.costs_model['cost_slope_USD_kW']
            b = self.costs_model['cost_int_USD']
            capex = a*self.energy_MAX_kW + b
            if self.has_components():
                comp_capex = 0
                for c in self.components:
                    comp_capex += self.components[c].get_capex()
                capex += comp_capex
            self.has_capex=True
        return capex

    def get_opex(self):
        opex=0
        self.size()
        if ~self.has_opex:
            #energy kW
            opex = electricity_cost_USD_yr(self.energy_kW,self.electricity_kwh)
            if self.has_components():
                comp_opex = 0
                for c in self.components:
                    comp_opex += self.components[c].get_opex()
                opex += comp_opex
            self.has_opex=True
        return opex

    def head_power_kW(self,H_kPa,Q_LPH):
        kW = H_kPa*Q_LPH*1/3600*1/1000
        return kW


def pipe_friction(Q_LPM,ID_cm,L_m,model='hueristic'):
    #input : flow Q in LPM, pipe ID in cm, pipe length L in m
    #output : friction head : kPa
    head_factor = 2.3
    v = pipe_velocity(Q_LPM,ID_cm)
    if model=='hueristic':
        head_factor = hueristic_friction_model(v)
    head = head_factor*L_m
    return head


def hueristic_friction_model(v):
    #input : velocity v in m/s
    #output : friction head per unit length : Pa/m
    global models
    mdl = models['hueristic_friction_head']
    head_factor = mdl['a']*(v-mdl['v0']) + mdl['hf0']
    return head_factor


def pipe_velocity(Q_LPM,ID_cm):
    #input : flow Q in LPM, pipe ID in cm
    #output : velocity in m/s
    A = cross_sectional_area(ID_cm/100) # in m
    v = Q_LPM/A*1/60000
    return v


def cross_sectional_area(D):
    A = math.pi*0.25*D**2
    return A


def electricity_cost_USD_yr(energy_kW,USD_kWh):
    annual_kWh = energy_kW*24*365
    return annual_kWh*USD_kWh