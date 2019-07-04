import pandas as pd
import numpy as np

fields = ['group','parameter','units','value']

class ParameterTable(pd.DataFrame):
    name = ''
    filepath = ''
    def __init__(self,df=None,filepath=None):
        if df is None:
            df = pd.read_csv(filepath)
        super(ParameterTable,self).__init__(df)
        if self.index.name!='parameter':
            self.set_index('parameter',inplace=True)
    def get(self,key):
        value = None
        if key in self.index:
            value = self.loc[key]['value']
        return value
        
