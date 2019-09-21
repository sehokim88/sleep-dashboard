import base64
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2 as pg
import os
from pandas.plotting import register_matplotlib_converters
from datetime import datetime
import scipy.stats as ss
register_matplotlib_converters()


host = os.getenv('RDS_HOST')
port = os.getenv('RDS_PORT')
database = os.getenv('RDS_DATABASE')
user = os.getenv('RDS_USER')
password = os.getenv('RDS_PASSWORD')
conn = pg.connect(host=host, port=port, database=database, user=user, password=password)
cur = conn.cursor()



query = """
SELECT start::time start_time,
    CASE WHEN EXTRACT( EPOCH FROM start::time ) < 60*60*12 THEN EXTRACT( EPOCH FROM start::time ) + 60*60*24
        ELSE EXTRACT( EPOCH FROM start::time )
        END::real/60 start_epoch,
    EXTRACT( week FROM "end"::date -1 )::int2 "week",
    "end"::date-1 "date"
FROM sleep
WHERE NOW()-("end"::date-1) < INTERVAL '6 months' AND user_id LIKE '7B%' AND "end"-start > INTERVAL '3.5 hours'
ORDER BY start;
"""

cur.execute(query)
data = cur.fetchall()
colnames = [cn[0] for cn in cur.description]
sleep_start_time_with_week = pd.DataFrame(data, columns=colnames)




weekly_avg_df = sleep_start_time_with_week.groupby('week').mean().reset_index()
weekly_std_df = sleep_start_time_with_week.groupby('week').std().reset_index()
weekly_stats_df = weekly_avg_df.merge(weekly_std_df, on='week')
weekly_stats_df.columns = ['week', 'avg', 'std']

get_time = lambda x: datetime.strftime(x,'%H:%M:%S')
weekly_stats_df['time'] = pd.to_datetime(weekly_stats_df['avg']*60, unit='s').apply(get_time)

last_ind = weekly_stats_df.shape[0]-2
overall_avg_std = weekly_stats_df.loc[:last_ind ,'std'].mean()
get_pct_change_from_overall = lambda x: (x - overall_avg_std) / overall_avg_std
weekly_stats_df['comp'] = weekly_stats_df['std'].apply(get_pct_change_from_overall)   




fig = plt.figure(figsize=(10,3))
grid = plt.GridSpec(1,1)
ax1 = plt.subplot(grid[0,0])

ax1.boxplot(
    weekly_stats_df.loc[weekly_stats_df.notna().all(1),'std'],
    labels=[''],
    widths=[0.25],
    vert=False,
    medianprops={'color':'black'}
)
ax1.set_title('Inconsistency Measure for Sleep Start Time')
ax1.set_xlabel('Inconsistency Measure (STD by Weeks in Minutes)')

for i, j in enumerate(list(range(-4,0))):
    size = np.exp(i+2)+10
    consistency_score = weekly_stats_df['std'].values[j]
    week = weekly_stats_df['week'].values[j]
    label= f"{week}th Week"
    if j == -1:
        color='red'
    else: color='black'
    ax1.scatter(consistency_score, 1, c=color, s=size, label=label, marker=',')
        
ax1.legend()

start_date = sleep_start_time_with_week['date'].values[0]
end_date = sleep_start_time_with_week['date'].values[-1]
fig.savefig(f'weekly-inconsistency-{start_date}-{end_date}.png', bbox_inches='tight')
print(f'plot saved as "weekly-inconsistency-{start_date}-{end_date}.png"')