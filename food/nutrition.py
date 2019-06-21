import pandas as pd
import sys
import numpy as np

isloaded = False
tables = {}
table_filenames = {'nutrition':'USDA_nutrition.csv',
                   'food_item':'FAO_USDA_item_map.csv',
                   'diets_global':'global_diets.csv',
                   'food_group_sgp':'food_group_sgp.csv',
                   'sgp_weights':'sgp_weights.csv',
                   'cho':'cho_composition.csv',
                   }

food_item_index = None
nut_matrix = None
chons_matrix = None
nut_fields = []
cho_groups = []
CHONS_labels = []

class Diet():
    label = ''
    year = 2013
    country = 'China'
    kg = None
    subdiets = None
    blend = None
    def __init__(self,kg,name='',year=2013,country='China',subdiets=None,blend=None):
        global tables
        load()
        self.kg = kg
        self.label = name
        self.year=year
        self.country = country
        self.subdiets = subdiets
        self.blend= blend
        
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

    def food_groups(self):
        df = None
        if not 'diet_group' in tables:
            create_diet_group_table()
        if self.blend is None:
            if has_diet_record(self.year,self.country):
                dietData = tables['diet_group']
                df = dietData[(dietData.year==self.year) &
                    (dietData.country==self.country)][['sgp group','amount kg_pa']]
                df = df.groupby('sgp group').sum()['amount kg_pa']
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

    def elements(self):
        global tables, chons_matrix, cho_groups, CHONS_labels
        elements = {}
        inorganics = ['water','Ca','K','P','Mg']
        fields = CHONS_labels + inorganics
        nt = self.nutrition()
        
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
    fields = ['year','country','nutrition id','sgp group','amount kg_pa']
    diets = tables['diets_global'] ;     fi = tables['food_item'] ; fg = tables['food_group_sgp']
    fi.rename(columns={'id':'FAO item'},inplace=True)
    df1 = pd.merge(diets,fi[['FAO item','nutrition id']],on='FAO item')
    df2 = pd.merge(df1,fg,on='nutrition id')[fields]
    tables['diet_group'] = df2

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

def load(refresh=False):
    global tables, table_filenames, isloaded
    if (not isloaded) or (isloaded and refresh):
        for tblName in table_filenames:
            tables[tblName] = pd.read_csv(table_filenames[tblName])
        tables['nutrition'].set_index('food item name',inplace=True)
        load_crop_data()
        set_food_item_index()
        set_nutrition_matrix()
        set_chons_matrix()

