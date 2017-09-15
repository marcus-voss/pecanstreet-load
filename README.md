# Dataport Pecan Street dataset

The provided scripts can be used to download and exploratively analyze the Dataport Pecan Street dataset. The data is provided by Dataport and Pecan Street Inc., and a key to access the data must be obtained from [https://dataport.cloud/](https://dataport.cloud/ "datapart").

## download\_pecanstreet.py

The script is currently setup to download the data for 2 years (2015-2016) for Boulder and Austin (the largest cities with available data) and also downloads the associated weather data. It fills holes of 3 hours by linear interpolation and holes larger than 3 hours to up a day by using the values of 24 hours before. If still N/A values are existing, the ID is dropped from the final results (resulting in 200 households for Austin and 20 households for Boulder). 

Resulting files output in *.csv format and as pickled Pandas dataframes (readable for Python 3). 

Datetime format is YYYY-MM-DD hh:mm:ss±hh:mm, where the part "±hh:mm" is the offset of UTC, hence the time is local time.

### Weather
Weather data is ouput per city and is of format:

- temperature (in °C)
- apparent_temperature (in °C)
- dew_point
- humidity
- visibility
- pressure
- wind_speed
- cloud_cover
- wind_bearing
- precip_intensity
- precip_probability

### Load
The output load files are one for each configured aggregation level. For single households one column per household is created and the id is the id used by the Pecanstreed database (see table *university.metadata* for properties of the households), for aggregations, which are created pseudo-randomly (with a seed), a increasing id is given. Load is in average kW per interval. The files are created for 15-min and hourly intervals.

## analyze\_pecan\_data.py

For each created load file, the script creates the following plots:

- Autocorrelation Plot (ACF)
- Scatter plot showing the correlation of temperature and load
- the trace of a week