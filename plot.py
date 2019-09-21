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
    CASE WHEN EXTRACT( EPOCH FROM start::time ) > 60*60*12 THEN EXTRACT( EPOCH FROM start::time )
        ELSE EXTRACT( EPOCH FROM start::time ) + 60*60*24
        END::real / 60 start_epoch,
    EXTRACT( DOW FROM "end"::date -1 )::int2 dow,
    "end"::date-1 "date"
FROM sleep
WHERE user_id LIKE '7B%' 
AND EXTRACT( EPOCH FROM "end"-start )::dec/60/60 >= 3
AND NOW() - ("end"::date-1) < INTERVAL '6 months'
ORDER BY start ASC;
"""
cur.execute(query)
data = cur.fetchall()
colname = [c[0] for c in cur.description]
sleep_start_with_dow = pd.DataFrame(data, columns=colname)










sun = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 0]
mon = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 1]
tue = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 2]
wed = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 3]
thu = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 4]
fri = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 5]
sat = sleep_start_with_dow.loc[sleep_start_with_dow['dow'] == 6]
most_recent_by_dow = []
dow_digits = []
for dow_digit, dow in enumerate([sun,mon,tue,wed,thu,fri,sat]):
    most_recent_by_dow.append(dow.reset_index().loc[dow.shape[0]-1, 'start_epoch'])
    dow_digits.append(dow_digit+1)
week_avg_start_time = np.mean(most_recent_by_dow)











fig = plt.figure(figsize=(10,6))
fig.subplots_adjust(hspace=0.4, wspace=0.4)
grid = plt.GridSpec(4,1)


ax1 = plt.subplot(grid[1:,0])
ax1.boxplot(
    [sun['start_epoch'].values,
     mon['start_epoch'].values,
     tue['start_epoch'].values,
     wed['start_epoch'].values,
     thu['start_epoch'].values,
     fri['start_epoch'].values,
     sat['start_epoch'].values],
    labels=['S', 'M', 'T', 'W', 'Th', 'F', 'Sa'],
    widths=0.5,
    vert=False,
#     showmeans=True,
    showfliers=False,
#     meanprops={'marker' : '+' , 'markerfacecolor' : 'r', 'markeredgecolor' : 'r'}
    medianprops={'color':'black'}
)

ax1.set_xticks(np.linspace(0,30*60,31))
ax1.set_xticklabels([datetime.utcfromtimestamp(t*60).strftime('%H:%M') for t in np.linspace(0,30*60,31)])
ax1.set_xlim(18*60, 31*60)
ax1.set_xlabel('Average Sleep Start Time')
ax1.set_ylabel('Day of the Week')

ax1.scatter(most_recent_by_dow, dow_digits, c='red', s=20, label='Most Recent Recordings', marker=',')
ax1.axvline(week_avg_start_time, linestyle='--', c='red', linewidth=0.5, label='AVG of the 7 Most Recent Recordings')
# ax1.axvline(21.5*60, linestyle='--', linewidth=0.5, label='sleep start goal')
ax1.legend()


ax2 = plt.subplot(grid[0,0], sharex=ax1)
ax2.boxplot(
    sleep_start_with_dow['start_epoch'],
    labels=['All'],
    widths=0.3,
    vert=False,
#     showmeans=True,
    showfliers=False,
#     meanprops={'marker' : '.' , 'markerfacecolor' : 'r', 'markeredgecolor' : 'r'}
    medianprops={'color':'black'}
)

# ax2.set_xticks(np.linspace(0,28*60,29))
# ax2.set_xticklabels([datetime.utcfromtimestamp(t*60).strftime('%H:%M') for t in np.linspace(0,28*60,29)])
# ax2.set_xlim(18*60, 29*60)
# ax1.set_ylabel('Day of the Week')
ax2.set_title('Sleep Start Time Distribution by DOW for the past 6 months')


start_date = sleep_start_with_dow['date'].values[0]
end_date = sleep_start_with_dow['date'].values[-1]
fig.savefig(f"sleep-start-dow-{start_date}-{end_date}.png", bbox_inches='tight')
print(f'plot saved as "sleep-start-dow-{start_date}-{end_date}.png"')