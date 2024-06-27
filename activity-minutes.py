import pandas as pd
import sys
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

age = 36
filter_by_meanhr = True
display_group_by_days = False
drop_garmin_measurements = True
pd.set_option('display.min_rows', 20)

######## start of script #########
activehr = 0.60 * (220 - age)
vigoroushr = 0.75 * (220 - age)

# DataFrame to read our input CS file
df = pd.read_csv(sys.argv[1], delimiter=',', header=1)
#print(f"\nInput CSV file = {df}\n")

# slice the relevant data fields
df = df[["sourceName", "startDate", "endDate", "value"]]

if drop_garmin_measurements:
    # only keep measurements from apple watch (drop "Connect" values)
    df = df.drop(df[df.sourceName == "Connect"].index)

# sorting according to endDate column
df.sort_values("endDate", axis=0, ascending=True, inplace=True, na_position='first')
#print(f"sorted dataframe = \n{df}")

# parse datetime and add a new duration column
df['endDate'] = pd.to_datetime(df['endDate'])
df['startDate'] = df.endDate.shift(1)
#df['startDate'] = pd.to_datetime(df['startDate'])
df['duration'] = df.apply(lambda row: row.endDate - row.startDate, axis=1)
df = df[["sourceName", "startDate",  "endDate", "duration", "value"]]
print(f"duration added = \n{df}")

# 10-minutes moving average
df = df.dropna()
df = df.set_index('startDate')
#df['hr_ten_minutes_before'] = df['value'].rolling(timedelta(minutes=10), closed='both').apply(lambda row: row.iloc[-1])
df['meanhr'] = df['value'].rolling(timedelta(minutes=10), closed='both').mean()
df = df.reset_index()
print(f"hr 10 minutes heart rate moving average = \n{df}")

# add a new hear rate column with values 10 minutes before (TODO: does not work yet)
#df = df.dropna()
#df = df.set_index('startDate')
#df['hr_ten_minutes_before'] = df.rolling(timedelta(minutes=10), closed='both')['value'].apply(lambda row: row.iloc[0])
#print(f"hr 10 minutes before added = \n{df}")
#sys.exit(0)

# calculate activity intensity score
df['score'] = df.apply(lambda row: 1 if row.value > activehr else 2 if row.value > vigoroushr else 0, axis=1)
if filter_by_meanhr:
    df['consider'] = df.apply(lambda row: 1 if row.meanhr > activehr else 0, axis=1)
    df['score'] = df.apply(lambda row: row.score * row.consider, axis=1)
df = df[["sourceName", "startDate",  "endDate", "duration", "value", "score"]]
print(f"score = \n{df}")

# caclulate intensity minutes
df['activity_minutes'] = df.apply(lambda row: row.score * row.duration if row.duration.total_seconds() > 0 and row.duration.total_seconds() < 900 else timedelta(seconds=0), axis=1)
df = df.drop(df[df.activity_minutes == timedelta(seconds=0)].index)
print(f"activity minutes = \n{df}")

# group by intervals of 10 minutes
#u = (df.assign(timestamp=df.startDate.dt.floor('20min'))
#       .groupby(pd.Grouper(key='startDate', freq='10min'))
#       .ngroup())
#df['ten_min_period'] = np.char.add('period_', (pd.factorize(u)[0] + 1).astype(str))
#df['mean_hr'] = df.apply(lambda row: row.
#df_test = df.assign(timestamp=df.startDate.dt.floor('20min'))
#print(f"test = \n{df_test}")
#df_agg_by_ten_min = df.groupby(df.ten_min_period).agg({'value': 'mean'}).reset_index()
#print(f"grouped by intervals of 10 minutes = \n{df_agg_by_ten_min}")

# group
if display_group_by_days:
    df_agg_day = df.groupby(df.startDate.dt.date).agg({'activity_minutes': 'sum'}).reset_index()
    df_agg_day['activity_minutes'] = df_agg_day.apply(lambda row: row.activity_minutes.total_seconds() / 60, axis=1)
    print(f"activity minutes grouped by day = \n{df_agg_day}")
    df_agg_day.plot.bar(x='startDate', y='activity_minutes')
    plt.show()

df_agg_week = df.groupby(df.startDate.dt.strftime('%W')).agg({'activity_minutes': 'sum'}).reset_index()
df_agg_week['activity_minutes'] = df_agg_week.apply(lambda row: row.activity_minutes.total_seconds() / 60, axis=1)
print(f"activity minutes grouped by week = \n{df_agg_week}")
clrs = ['red' if (x < 150) else 'blue' for x in df_agg_week['activity_minutes']]
ax = df_agg_week.plot.bar(x='startDate', y='activity_minutes', color=clrs)
ax.set_xlabel("week")
plt.axhline(y=150, color='r', linestyle='-')
ax.set_ylabel("activity minutes [min]")
plt.show()