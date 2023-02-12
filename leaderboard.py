'''grab the to n all time countries'''
import logging

import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import numpy as np

from time_series import read_data

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__ )
n=30

lb_file='data/leader_board.xlsx'
df=read_data()
logger.info ('Number of rows is: %d'% df.shape[0])
df['Total']=df.sum(axis=1)
df.sort_values(by='Total',ascending=False,inplace=True)
print(df.head(n))

df.to_excel(lb_file)
logger.info('Wrote ' + lb_file)

del df['Total']
df.fillna(0,inplace=True)

month = df.columns.tolist()
labels=[]
month=['%d-%02d'%(divmod(m,100)) for m in month]
df.columns=month
outlier=False
if outlier:
  for ix,row in df.head(1).iterrows():
    vals=row.tolist()
    country='United States'
    if ix==country: # hack to adjust outlier
      x=vals.index(8645)
      df.at[country,month[x]]=2000

ax=df.head(12).T.plot.bar(rot=70, stacked=True)
ax.figure.set_size_inches(10,7)
ax.set_title('BoK Usage')
ax.set_xlabel('Month')
ax.set_ylabel('Number of downloads')
plt.savefig('data/leader_usage.png')
#plt.show()
