import pandas as pd
import sys
import numpy as np

isloaded = False
tables = {}
PKG_FOLDER = 'food/'
table_filenames = {'nutrition':'USDA_nutrition.csv',
                   'food_item':'FAO_USDA_item_map.csv',
                   'diets_global':'global_diets.csv',
                   'food_group_sgp':'food_group_sgp.csv',
                   'sgp_weights':'sgp_weights.csv',
                   'cho':'cho_composition.csv',
                   'food_waste':'food_waste.csv',
                   }

DECIMAL_PR = 3
food_item_index = None
nut_matrix = None
chons_matrix = None
nut_fields = []
cho_groups = []
CHONS_labels = []
FATS = ['sat fats','mono unsaturated','polyunsaturated']
ORG_COMPONENTS = ['carbs','fats','protein','fiber','minerals','water']
MINERALS = ['Ca','K','P','Mg','Vit B12']

class Organic(object):
    label = ''
    comp = None
    def __init__(self,components):
        global DECIMAL_PR
        self.comp = components.round(DECIMAL_PR)

    def __eq__(self,other):
        return all(self.comp==other.comp)

    def __add__(self,other):
        x = self.comp+other.comp
        org = Organic(x)
        return org

    def __radd__(self,other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __sub__(self,other):
        x = self.comp-other.comp
        org = Organic(x)
        return org

    def wet_basis(self):
        global MINERALS, ORG_COMPONENTS
        nt = self.comp.copy()
        x = {}
        for cmp in [x for x in ORG_COMPONENTS if not x in ['minerals','fats']]:
            x[cmp] = nt[cmp]
        x['minerals'] = sum([nt[z] for z in nt.index if z in MINERALS])*10**-3
        x['fats'] = sum([nt[z] for z in nt.index if z in FATS])
        x = pd.Series(x)
        x.name = 'wet_basis'
        return x        

    def dry_basis(self):
        x = self.wet_basis().copy()
        x.name = 'dry_basis'
        x.drop('water',inplace=True)
        return x

    def wt_g(self,basis='wet'):
        if basis == 'wet':
            x = self.wet_basis()
        else:
            x = self.dry_basis()
        return x.sum()

    def elements(self):
        global tables, chons_matrix, cho_groups, CHONS_labels
        elements = {}
        inorganics = ['water','Ca','K','P','Mg']
        fields = CHONS_labels + inorganics
        nt = self.comp.copy()
        
        #direct assignment
        for x in ['water','Ca','K']:
            elements[x] = nt[x]

        #apply chons matrix
        nt_matrix = nt[cho_groups].as_matrix()
        chons = np.dot(chons_matrix,nt_matrix)
        for i in range(len(CHONS_labels)):
            elements[CHONS_labels[i]] = chons[i]

        #arbitrary mineral estimation
        elements['P'] = nt['K']
        elements['Mg'] = 0.5*nt['K'] + 0.5*nt['Ca']
       
        df = pd.DataFrame({'element':fields,'amount':[elements[x] for x in fields]})
        df.set_index('element',inplace=True)
        return df['amount']
    
    def cn_ratio(self):
        ratio = 0
        el = self.elements()
        if el['N'] != 0:
            ratio = el['C']/el['N']
        return ratio

class Diet(Organic):
    year = 2013
    country = 'China'
    kg = None
    subdiets = None
    blend = None
    def __init__(self,kg,name='',year=2013,country='China',subdiets=None,blend=None):
        global tables, DECIMAL_PR
        load()
        self.kg = kg.round(DECIMAL_PR)
        self.label = name
        self.year=year
        self.country = country
        self.subdiets = subdiets
        self.blend= blend
        nut_kg = self.nutrition().copy()
        del nut_kg['fats'], nut_kg['crop area m2']
        super(Diet,self).__init__(nut_kg)
        
    @classmethod
    def from_country(cls,year,country,name=''):
        load()
        kg = get_kg_by_country(year,country)['amount kg_pa']
        if name=='':
            name = country_label(year,country)
        return cls(kg,name,year,country)
        
    @classmethod        
    def from_blend(cls,weights,name='blend'):
        load()
        rcds = [x for x in weights.to_records()]
        diets = [Diet.from_country(x[1],x[2]) for x in rcds]
        kg = sum([diets[i].kg*rcds[i][3] for i in range(len(rcds))])
        return cls(kg,name,None,None,subdiets=diets,blend=weights)
        
    def __repr__(self):
        return '<Diet : %s>' % self.label

    def __eq__(self,other):
        if isinstance(other,Diet):
            cmp = all(self.kg==other.kg)
        elif isinstance(other,Organic):
            cmp = all(self.comp==other.comp)
        return cmp

    def __add__(self,other):
        if isinstance(other,Diet):
            x = self.kg+other.kg
            d = Diet(x)
        elif isinstance(other,Organic):
            x = self.comp+other.comp
            d = Organic(x)
        return d

    def __sub__(self,other):
        if isinstance(other,Diet):
            x = self.kg-other.kg
            d = Diet(x)
        elif isinstance(other,Organic):
            x = self.comp-other.comp
            d = Organic(x)
        return d

    def food_groups(self):
        df = None
        if not 'diet_group' in tables:
            create_diet_group_table()
        if self.blend is None:
            dietData = tables['diet_group']
            kg_df = pd.DataFrame(self.kg).reset_index()
            df = pd.merge(kg_df,dietData,on='FAO item')
            df = df.groupby('component').sum()['amount kg_pa']
        else:
            rcds = [x for x in self.blend.to_records()]
            df = sum([self.subdiets[i].food_groups()*rcds[i][3] for i in range(len(rcds))])
        return df

    def nutrition(self):
        x = np.matrix(self.kg)*10/365     #100 g / day
        dt = [x[0] for x in np.dot(nut_matrix,x.transpose()).tolist()]
        df = pd.DataFrame({'nutrient':nut_fields,'amount':dt},
            columns=['nutrient','amount'])
        df.set_index('nutrient',inplace=True)
        return df['amount']

def country_label(year,country):
    label = '%s_%s' %(country,year)
    return label

def get_kg_by_country(year,country):
    global nut_fields, tables
    df = None
    if has_diet_record(year,country):
        dietData = tables['diets_global']    
        df = dietData[(dietData.year==year) & (dietData.country==country)]
        df = df[[x for x in df.columns if not x in ['year','country']]]
        df.set_index('FAO item',inplace=True)
    return df
        
def set_nutrition_matrix():
    global nut_matrix, nut_fields
    cropData = tables['crop_data']
    categorical_fields = ['nutrition id','name','group','crop group']
    cropData = cropData[[x for x in cropData.columns if not x in categorical_fields]].copy()
    cropData.set_index('id',inplace=True)
    cropData['crop area m2'] = cropData.apply(
        lambda x:1/x['yield']*100000/365 if (x['yield']>0 and not pd.isnull(x['yield'])) else 0,axis=1)
    del cropData['yield']
    nut_matrix = np.nan_to_num(np.matrix(cropData.loc[food_item_index]).transpose())
    nut_fields = cropData.columns

def create_diet_group_table():
    global tables
    fi = tables['food_item']
    fg = tables['food_group_sgp']
    df = pd.merge(fi,fg,on='nutrition id')[['id','sgp group']]
    df.rename(columns={'id':'FAO item','sgp group':'component'},inplace=True)
    tables['diet_group'] = df

def has_diet_record(year,country):
    global tables
    dietData = tables['diets_global']    
    has_year = year in dietData.year.unique()
    has_country = country in dietData.country.unique()
    has_record = (has_year and has_country)
    return has_record

def sgp_diet():
    load()
    global tables
    w = tables['sgp_weights']
    blend = Diet.from_blend(w,name='SGP')
    return blend

def set_chons_matrix():
    global tables, chons_matrix, cho_groups, CHONS_labels
    choRcds = tables['cho']
    cho_groups = ['sat fats','mono unsaturated',
        'polyunsaturated','carbs','fiber','protein']
    CHONS_labels = ['C','H','O','N','S']
    chons_pvt = pd.pivot_table(choRcds,values='wt',
        index='element',columns='nutrition group')
    chons_matrix = chons_pvt[cho_groups].loc[CHONS_labels].as_matrix()

def set_food_item_index():
    global food_item_index
    food_item_index=tables['diets_global']['FAO item'].unique()

def load_crop_data():
    tables['crop_data'] = pd.merge(tables['food_item'],tables['nutrition'],on='nutrition id')

def get_nutrition(item_name,nutrient):
    global tables
    nutData = tables['nutrition']
    content = None
    has_item = item_name in nutData.index
    has_field = nutrient in nutData.columns
    if (has_item and has_field):
            content = nutData.loc[item_name][nutrient]
    return content        

def get_waste(d):
    #doesn't include sewage - urine/feces
    ows = []
    #01 collect upstream - cooking prep, spoilage
    (w1,ups) = get_step_waste(d,'cooking preparation',None,False,True) 
    ows.append(w1)
    w2 = get_step_waste(ups,'spoilage',None,False)
    ows.append(w2)
    #02 collect downstream - served
    w3 = get_step_waste(d,'serving',None,True)
    ows.append(w3)
    #03 compile together
    waste = sum(ows)
    return waste    

def get_step_waste(d,process,z=None,forward=True,upstream=False,base=True):
    global tables
    fw = tables['food_waste'][tables['food_waste'
            ].process==process][[x for x in tables['food_waste'] if not x =='process']]
    cl = fw.classification.unique()[0]
    fw = fw[[x for x in fw.columns if not x =='classification']]
    if z is None:
        if cl == 'food groups':
            #01 c0: allocate the food waste splits into individual food items
            if not 'diet_group' in tables:
                create_diet_group_table()
            df = tables['diet_group']
            c0 = pd.merge(df,fw,on='component')[['FAO item','waste pct']]
            c0.set_index('FAO item',inplace=True)
            c0 = c0['waste pct']
            if base:
                #02 fx: normalize by food items
                if isinstance(d,Diet):
                    fx = d.kg/d.kg.sum()
                else:
                    sgp = sgp_diet()
                    fx = sgp.kg/sgp.kg.sum()
                #03 b = c0*fx
                b = c0.loc[fx.index]*fx
                c = np.dot(nut_matrix*1/100,b.as_matrix())
                #04 pct = filter relevant fields from comp
                pct = pd.Series(dict(zip(nut_fields,c.tolist()[0])),name='waste pct')
                z = pct.loc[d.comp.index]
            else:
                pct = c0['waste pct']
                z = pct.loc[d.kg.index]
        elif cl == 'nutrition':
            fw = fw.set_index('component')['waste pct']
            fz = {}
            for x in [z for z in d.comp.index if z in FATS]:
                fz[x] = fw.fats
            for x in [z for z in d.comp.index if z in MINERALS]:
                fz[x] = fw.minerals
            for x in [z for z in d.comp.index if not z in FATS+MINERALS]:
                fz[x] = fw[x]
            pct = pd.Series(fz,name='waste pct')
            z = pct.loc[d.comp.index]
        if upstream:
            (waste,ups) = get_step_waste(d,process,z,forward,upstream,base)
        else:
            waste = get_step_waste(d,process,z,forward,upstream,base)
    else:
        if cl == 'food groups' and not base:
            x = d.kg 
        else:
            x = d.comp
        if forward:
            w_kg = x*z
            u = x
        else:
            w_kg = x*z/(1-z)
            u = x/(1-z)
        w_kg.fillna(0,inplace=True)
        u.fillna(0,inplace=True)
        w_kg.name = 'amount kg_pa'
        u.name = 'amount kg_pa'
        if base:
            waste = Organic(w_kg)
            ups = Organic(u)
        else:
            waste = Diet(w_kg)
            ups = Diet(u)
    if upstream:
        return (waste,ups)
    else:
        return waste

def load(refresh=False):
    global tables, table_filenames, isloaded, PKG_FOLDER
    if (not isloaded) or (isloaded and refresh):
        for tblName in table_filenames:
            tables[tblName] = pd.read_csv(PKG_FOLDER + table_filenames[tblName])
        tables['nutrition'].set_index('food item name',inplace=True)
        load_crop_data()
        set_food_item_index()
        set_nutrition_matrix()
        set_chons_matrix()

