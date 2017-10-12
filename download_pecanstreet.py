__author__ = 'voss'

from random import shuffle, seed
import pandas as pd
import pytz
import sys
from datetime import datetime
from sqlalchemy import create_engine  # worked using the win.exe file from homepage and easy_install
import os

seed( 42 ) # seed for random shuffling to groups

# setup
start_date = "2015-01-01"
end_date = "2017-01-01"

freqs = ["15min", "H"]
locations = ["austin", "boulder"]

latitudes = {"austin": 30.292432,       # (30.292432,-97.699662)
             "boulder" : 40.027278      # (40.027278,-105.256111)
             }

# sizes of aggregations to create
sizes = [10, 20, 50, 100, 200] 

utc = pytz.timezone("UTC")
tzs = {
       "boulder" : pytz.timezone("US/Mountain"),
       "austin"  : pytz.timezone("US/Central")
       }

# dirty ids
dirty = [8282]

# create database connection and queries
# exchange XXXX:XXXXX with authentication 
engine = create_engine('postgresql://XXXXXXX:XXXXXX@dataport.pecanstreet.org:5434/postgres')
queries= {
        "15min" : "SELECT local_15min, use FROM university.electricity_egauge_15min WHERE local_15min >= \'%s\' and local_15min < \'%s\' and dataid=%s order by local_15min",
        "H"     : "SELECT to_char(localhour, 'MM-DD-YYYY HH24:MI:SS') as time, use FROM university.electricity_egauge_hours WHERE localhour >= \'%s\' and localhour < \'%s\' and dataid=%s order by localhour"
        }

# select the households that have minimum and maximum in the date range
print("Downloading meta-data")
meta_df = pd.read_sql_query("SELECT * FROM university.metadata", con=engine)
meta_df["egauge_max_time"] = pd.to_datetime(meta_df["egauge_max_time"], utc=True)
meta_df["egauge_min_time"] = pd.to_datetime(meta_df["egauge_min_time"], utc=True)
meta_df = meta_df[(meta_df.egauge_max_time >= end_date) & (meta_df.egauge_min_time <= start_date)]

# set the ids as index and shuffle the ids
meta_df = meta_df.set_index(meta_df.dataid)
ids = {}
for l in locations:
    ids[l] = meta_df[(meta_df.use == "yes") & (meta_df.city.str.lower() == l) & (~meta_df.dataid.isin(dirty))].dataid.tolist()
    print("There are %d households in %s" % (len(ids[l]), l))

# get the load data
for f in freqs:
    print("Starting for frequency %s" % f)
    for l in locations:
        print("Starting for location %s" % l)
        df_index = pd.date_range(start=tzs[l].localize(datetime.strptime(start_date, "%Y-%m-%d")), end=tzs[l].localize(datetime.strptime(end_date, "%Y-%m-%d")), freq=f, tz=tzs[l], closed="left")
        df = pd.DataFrame(index=df_index)
        for id in ids[l]:
            try:
                # query the data the data
                load = pd.read_sql_query(queries[f] % (start_date, end_date, id), con=engine)
                load["time"] = load.iloc[:, 0]
                
                # it is localtime so localize it correctly
                load["time"] = pd.to_datetime(load["time"], utc=True)
                load["time"] = load["time"].apply(lambda x: tzs[l].localize(x).astimezone(tzs[l]))
                
                # make it index
                load = load.set_index(load["time"])
                load.drop(['time'], 1, inplace=True)  # is already index              
                load = load[~load.index.duplicated(keep='first')] # handle their stupid handling of summertime
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print("There was an errror with id: " + str(id) + ", Error: " + str(e.args), " in line: " + str(exc_tb.tb_lineno))
                continue
            df[id] = load.use
        
        # interpolate small gaps (e.g. for summertime change)
        df = df.interpolate(limit=3 if f == 'H' else 12)
        
        # fix larger holes
        for c in df:
            df[c] = df[c].fillna(value=df[c].shift(24 if f == 'H' else 96)) 
        
        # drop if still n/a
        before = df.shape[1]
        df = df.dropna(axis=1, how="any")
        print("Had to drop for %s and %s: %d" % (f, l, before - df.shape[1]))
        
        csv_path = "./csv/" + l + "/" + f
        pickle_path = "./pickle/" + l + "/" + f
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        if not os.path.exists(pickle_path):
            os.makedirs(pickle_path)
        
        df.to_csv(csv_path + "/%s_%s_load.csv" % (l, f), float_format='%.3f')
        
        # produce higher aggregations as available
        for s in sizes:
            agg = pd.DataFrame(index=df.index)
            counter = 1
            for i in range(0,df.shape[1] - (df.shape[1] % s),s):
                agg[str(s) + "_" + str(counter)] = df.iloc[:,i:i+s].sum(axis=1)
                counter += 1
            if agg.shape[1] > 0:
                agg.to_csv(csv_path + "/%s_%s_load_agg_%s.csv" %  (l, f, s), float_format='%.3f')
                agg.to_pickle(pickle_path + "/%s_%s_load_agg_%s.p" % (l, f, s))


# query the weather data, converting fahrenheit to celsius
weather_query = "select localhour, (temperature - 32) /  1.8 as temperature, (apparent_temperature - 32) /  1.8 as apparent_temperature, dew_point, humidity, visibility, pressure, wind_speed, cloud_cover, wind_bearing, precip_intensity, precip_probability from university.weather where localhour >= \'%s\' and localhour < \'%s\' and latitude = %f order by localhour"
for l in locations:
    index = pd.date_range(start=tzs[l].localize(datetime.strptime(start_date, "%Y-%m-%d")), end=tzs[l].localize(datetime.strptime(end_date, "%Y-%m-%d")), freq="H", tz=tzs[l], closed="left")
    print("Downloading weather for location %s" % l)
    weather = pd.read_sql_query(weather_query % (start_date, end_date, latitudes[l]), con=engine)
    
    # make proper timeindex 
    weather["time"] = pd.to_datetime(weather["localhour"], utc=True)
    weather["time"] = weather["time"].apply(lambda x: utc.localize(x).astimezone(tzs[l]))
    weather = weather.set_index(weather["time"])
    weather = weather.drop(["time", "localhour"], axis=1)
    weather = weather[~weather.index.duplicated(keep='first')]
    weather = weather.reindex(index) # to handle their stupdid summer time handling
    weather = weather.interpolate(limit=3) # small holes
    # larger holes
    for c in weather:
        weather[c] = weather[c].fillna(value=weather[c].shift(24)) 
    
    # store
    weather.to_csv("./csv/" + l + "/%s_weather.csv" % (l), float_format='%.2f')
    weather.to_pickle("./pickle/" + l + "/%s_weather.p" % (l))
