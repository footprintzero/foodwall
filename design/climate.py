from sqlalchemy import create_engine
import pandas as pd
from pyppfd import solar as solar

engine = None
SQL_DB_NAME = 'sqlite:///foodwall.db'
SQL_CLIMATE_TABLE = 'climate'
CLIMATE_CSV_FILENAME = 'design\\climate_hourly.csv'
CLIMATE_TABLE_FIELDS = ['hour','T DEG C','RH','month',
                        'irradiance W/m2','ppfd umol/m2/s','location name']
STATS = ['24hr_avg','24hr_max','day_avg','night_avg']
STAT_FIELDS = ['T_C','RH','irradiance_W_m2','ppfd_umol_m2_s']

default_params = {'daylight_hpd':12,
                  'angle_max':90,
                  'cloud_cover':0.25,
                  'rainfall_mm_wk':40,
                  'resolution_hrs': 3,
                  'location_name': 'Singapore',
                  'climate_month': 7,
                  }


case_params = {}

def setup():
    global case_params, default_parameters
    case_params = default_params.copy()


def update(params=None):
    setup()
    global case_params
    if params is not None:
        for p in params:
            case_params[p] = params[p]
    run()
    return case_params.copy()

def run():
    load()
    set_daily_statistics()

def load():
    global engine
    if engine is None:
        engine = create_engine(SQL_DB_NAME,echo=False)

def get_climate_data():
    global engine
    load()
    qrystr = 'select * from ' + SQL_CLIMATE_TABLE
    tbl = pd.read_sql(qrystr,con=engine)
    return tbl

def set_daily_statistics(**kwargs):
    global case_params, STATS
    for stat in STATS:
        case_params[stat] = get_daily_statistics(stat,**kwargs)

def get_daily_statistics(stat='daily_avg',**kwargs):
    # STAT_FIELDS = ['T_C', 'RH', 'irradiance_W_m2', 'ppfd_umol_m2_s']
    global case_params, STAT_FIELDS, CLIMATE_TABLE_FIELDS
    tbl_args = ['location_name','climate_month']
    model_args = ['daylight_hpd']
    for arg in model_args+tbl_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    location_name = kwargs['location_name']
    climate_month = kwargs['climate_month']
    cltbl = get_climate_data()
    cltbl = cltbl[(cltbl['location name']==location_name)&
              (cltbl['month']==climate_month)].copy()
    cltbl.set_index('hour',inplace=True)
    tbl_fields = [x for x in CLIMATE_TABLE_FIELDS if not x in
                    ['location name','month','hour']]
    half_day = int(0.5*kwargs['daylight_hpd'])
    values = []
    for field in tbl_fields:
        field_value = 0
        if stat == '24hr_avg':
            field_value = cltbl[field].mean()
        elif stat == '24hr_max':
            field_value = cltbl[field].max()
        elif stat == 'day_avg':
            field_value = cltbl[field].loc[12-half_day:12+half_day].mean()
        elif stat == 'night_avg':
            morning_value = cltbl[field].loc[:12-half_day].mean()
            night_value = cltbl[field].loc[12+half_day:].mean()
            field_value = 0.5*(morning_value+night_value)
        values.append(field_value)
    stats = dict(zip(STAT_FIELDS,values))
    return stats

def add_solar_records(**kwargs):
    global case_params
    model_args = ['location_name','climate_month']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    location_name = kwargs['location_name']
    climate_month = kwargs['climate_month']
    cltbl = get_climate_data()
    cltbl = cltbl[(cltbl['location name']==location_name)&
              (cltbl['month']==climate_month)].copy()
    solar_records = create_solar_records(cltbl.hour,**kwargs)
    tbl = pd.merge(cltbl,solar_records,on='hour')
    tbl.to_sql(SQL_CLIMATE_TABLE, con=engine, if_exists='replace',index=False)


def create_solar_records(hours,**kwargs):
    global case_params
    model_args = ['daylight_hpd','angle_max','cloud_cover','climate_month']
    for arg in model_args:
        if not arg in kwargs:
            kwargs[arg] = case_params[arg]
    daylight_hpd = kwargs['daylight_hpd']
    angle_max = kwargs['angle_max']
    cloud_cover= kwargs['cloud_cover']
    climate_month = kwargs['climate_month']
    irradiance_W_m2 = [solar.irradiation_by_hour(h,daylight_hpd=daylight_hpd,
                        angle_max=angle_max,cloud_cover=cloud_cover,
                        doy=climate_month/12*360)for h in hours]
    ppfd_umol_m2_s = [solar.photon_flux_by_hour(h,daylight_hpd=daylight_hpd,
                        angle_max=angle_max,cloud_cover=cloud_cover,
                        doy=climate_month/12*360)for h in hours]
    solar_records = pd.DataFrame({'hour':hours,'irradiance W/m2':irradiance_W_m2,
                                  'ppfd umol/m2/s':ppfd_umol_m2_s})
    return solar_records


def get_hours(res_hrs=3):
    hours = [x+0.5*res_hrs for x in range(0,24,res_hrs)]
    return hours


def add_climate_records():
    global engine
    load()
    tbl = pd.read_csv(CLIMATE_CSV_FILENAME)
    tbl.to_sql(SQL_CLIMATE_TABLE,con=engine,if_exists='replace',index=False)


#'daily_avg': {'irradiance_W_m2': [], 'ppfd': [],
#              'pro_T_C': [], 'pro_RH': [],
#              'transpiration_pl_ml_hr': [], 'ps_molCO2_pl_hr': []},

#'daily_max': {'irradiance_W_m2': [], 'ppfd': [],
#              'pro_T_C': [], 'pro_RH': [],
#              'transpiration_pl_ml_hr': [], 'ps_molCO2_pl_hr': []},

#'24hr_data': {'irradiance_W_m2': [], 'ppfd': [],
#              'pro_T_C': [], 'pro_RH': [],
#              'transpiration_pl_ml_hr': [], 'ps_molCO2_pl_hr': []},

