from sqlalchemy import create_engine
import pandas as pd

engine = None
simeng = None
SQL_DB_NAME = 'sqlite:///foodwall.db'
SQL_SIM_DB = 'sqlite:///simulation.db'
PARAM_TABLE = 'parameters'

def load():
    global engine,simeng
    if engine is None:
        engine = create_engine(SQL_DB_NAME,echo=False)
    if simeng is None:
        simeng = create_engine(SQL_SIM_DB,echo=False)

def create_simulation_db(import_param_tbl=False):
    global simeng, engine
    simeng = create_engine(SQL_SIM_DB, echo=False)
    if import_param_tbl:
        tbl = pd.read_sql('select * from ' + PARAM_TABLE,con=engine)
        tbl.to_sql(PARAM_TABLE,con=simeng,if_exists='replace')