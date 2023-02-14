#! /usr/bin/env python
'''grab the to n all time countries'''
import logging

import matplotlib.pyplot as plt

from time_series import read_data
out_file='docs/leader_usage.png'
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__ )
N=20

lb_file='data/leader_board.xlsx'
df=read_data()
logger.info ('Number of rows is: %d'% df.shape[0])
df['Total']=df.sum(axis=1)
df.sort_values(by='Total',ascending=False,inplace=True)
print(df.head(N))

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
  for ix,row in df.head(N).iterrows():
    vals=row.tolist()
    country='United States'
    if ix==country: # hack to adjust outlier
      x=vals.index(8645)
      df.at[country,month[x]]=2000

ax=df.head(N).T.plot.bar(rot=70, stacked=True)
ax.figure.set_size_inches(10,7)
ax.set_title('BoK Usage')
ax.set_xlabel('Month')
ax.set_ylabel('Number of downloads')
plt.savefig(out_file)
logger.info('Leader graphic saved to %s'%(out_file))
