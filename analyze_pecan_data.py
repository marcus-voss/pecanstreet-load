__author__ = 'voss'

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import os
import numpy as np
import seaborn as sns
from statsmodels.tsa.stattools import acf

utc = pytz.timezone("UTC")
tz = {"Boulder" : pytz.timezone("US/Mountain"),
    "Austin" : pytz.timezone("US/Central") }

matplotlib.style.use('ggplot')
#fformat = "pdf"
fformat = "png"

cities = ["Boulder", "Austin"]

weekdayFormat = mdates.DateFormatter('%a')
dateFormat = mdates.DateFormatter('%y-%m-%d')

# set plot properties
def style_plot():
    plt.tight_layout()
    plt.style.use("seaborn-white")
    sns.set(style="white")
    sns.despine(left=True)


for city in cities:
    weather = pd.read_pickle("pickle/" + city + "/%s_weather.p" % city.lower())  
    path = "pickle/" + city + "/H/"
    for f in os.listdir(path):
        load = pd.read_pickle(path + "/" + f)
        # read the aggregation level
        if "_agg_" in f:
            s = int(f.split("_agg_")[1].replace(".p", ""))
        else:
            s = 1
               
        #iterate over households or aggregations
        for h in load:
            # join load and weather
            df = load.loc[:,[h]].merge(weather[["temperature"]], left_index=True, right_index=True)
            df.columns = ["active_power", "temperature"]
    
            # create a output path
            out_path = "outputs/" + city.lower() + "/"+ str(s)
            if not os.path.exists(out_path):
                os.makedirs(out_path)

            # week profile
            fig, ax = plt.subplots(1, figsize=(16, 4))
            df_week = df["2015-01-05":"2015-01-11"]
            df_week["active_power"].plot(label='big')
            plt.xlabel('')
            plt.ylabel('kW')
            ax.xaxis.set_major_formatter(dateFormat)
            ax.xaxis.set_minor_formatter(weekdayFormat)
            # ax.fmt_xdata = mdates.DateFormatter('%a')
            style_plot()
            plt.savefig(out_path + "/week" + str(h) + "." + fformat, format=fformat, pad_inches=0.0, bbox_inches='tight')

            # ACF / PACF
            fig, ax = plt.subplots(1, figsize=(16, 4))
            lag_acf = acf(df["active_power"], nlags=180)
            ax.plot(lag_acf, linewidth=0.8, label='big')
            ax.axhline(y=-1.96 / np.sqrt(len(lag_acf)), linestyle='--', color='gray', linewidth=0.5)
            ax.axhline(y=1.96 / np.sqrt(len(lag_acf)), linestyle='--', color='gray', linewidth=0.5)
            ax.set_xlabel("Lag")
            ax.set_ylabel("Autocorrelation (ACF)")
            ax.set_xlim((0, 180))
            ax.xaxis.set_ticks([24, 48, 72, 96, 120, 144, 168])
            ax.legend()
            style_plot()
            plt.savefig(out_path + "/acf" + str(h) + "." + fformat, format=fformat, pad_inches=0.0, bbox_inches='tight')

            # correlation with temp
            fig, ax = plt.subplots(1, figsize=(16, 4))
            sns.lmplot(x='temperature',y='active_power',data=df, scatter_kws={"s": 10})
            style_plot()
            plt.savefig(out_path + "/correlation" + str(h) + "." + fformat, format=fformat, pad_inches=0.0, bbox_inches='tight')