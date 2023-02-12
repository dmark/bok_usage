'''read time series data'''

import logging
import os
import sys

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__ )

def base_12(yyyymm) -> int:
  'convert yyyymm to base 12'
  ym=yyyymm-1
  y=ym//100
  m=ym % 100
  r=1+m+y*12
  return r

def read_data():
  '''Read the data from the csv files exported from Janeway
  returns: a dataframe with monthly values with the country as index'''
  file_path='data/'
  files=os.listdir(file_path)
  files.sort()
  data=pd.DataFrame(columns=['Country'])
  months_12=[] # months base 12 for continuity check
  for file_name in files:
    if file_name.startswith('bok_geo_use_'):
      month=file_name.split('_')[-1].split('.')[0]
      try:
        month=int(month)
        months_12.append(base_12(month))
      except ValueError:
        logger.error('Bad file name: %s' % (file_name))
        sys.exit(-1)
      df=pd.read_csv(file_path+file_name,sep=',',encoding='utf-8')
      df.dropna(axis=0,how='any',inplace=True)
      df.rename(mapper={'Count':month},axis=1,inplace=True)
      data=data.merge(df,how='outer',on='Country')
  data=data.set_index('Country')
  if not (np.diff(months_12)==1).all():
    logger.error('File set is not contiguous months')
    sys.exit(-2)
  data.fillna(0,inplace=True)
  logger.info('Data read for %d months'% len(months_12))
  return data

if __name__=='__main__':
  df=read_data()
  print (df)
