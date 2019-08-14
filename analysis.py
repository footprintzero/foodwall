from design import database as db
import seaborn as sb
import pandas as pd

#load database and query the case table
db.load()
tbl = pd.read_sql('select * from cases',con=db.simeng)

#create the pivot table of all good (not null) cases
bad_caseids = tbl[pd.isnull(tbl.value)].caseid.unique()
goodtbl = tbl[~tbl.caseid.isin(bad_caseids)].copy()
pvt = pd.pivot_table(goodtbl, index='caseid',values='value', columns='parameter', aggfunc='mean')

#plot kde harvest extension vs costs
sb.jointplot(x='plants_harvest_extension',y='opex',data=pvt,kind='kde')