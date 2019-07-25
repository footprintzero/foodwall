import math
STD_PROCESS_EQ = ['tank','vessel','mixer','furnace','dosing','pump','blower']
COSTMODEL_ARGS = {'tank':{'wall_matl_USD_m2':45,
                          'thickness_scale_exp':0.85,
                          'cost_model':'surface_area',
                          },
                  'mixer': {
                          'cost_slope_USD_kW': 150,
                          'cost_int_USD': 2000,
                            }
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
    consumables = 0
    has_dimensions = False
    has_costs = False
    def __init__(self,load_size,load_basis='kgph',name='',eqp_type='tank',**kwargs):
        self.load_size = load_size
        self.load_basis = load_basis
        self.name = name
        self.eqp_type = eqp_type
        self.set_defaults()
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
        self.load_rate_kgph = load_rate_kgph
        self.turnover_days = turnover_days
        super(TankEqp,self).__init__(load_rate_kgph,load_basis='kgph',eqp_type=eqp_type,**kwargs)

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
        if ~self.has_costs:
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
            self.has_costs=True
        return capex

class MixerEqp(Equipment):
    load_rate_kgph = 0
    energy_kW = 0
    def __init__(self,load_rate_kgph,**kwargs):
        eqp_type = 'mixer'
        self.load_rate_kgph = load_rate_kgph
        super(MixerEqp,self).__init__(load_rate_kgph,load_basis='kgph',eqp_type=eqp_type,**kwargs)

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
            self.has_dimensions=True


    def get_capex(self):
        capex=0
        self.size()
        if ~self.has_costs:
            a = self.costs_model['cost_slope_USD_kW']
            b = self.costs_model['cost_int_USD']
            capex = a*self.energy_kW + b
            if self.has_components():
                comp_capex = 0
                for c in self.components:
                    comp_capex += self.components[c].get_capex()
                capex += comp_capex
            self.has_costs=True
        return capex