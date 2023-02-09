#! /usr/bin/env python
'''Main program to create country chart based on usage data from Janeway'''

import json
import logging
import math
import os
import sys

import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import geopy.extra.rate_limiter as rl
import numpy as np
import pandas as pd

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
  if not np.diff(months_12).all():
    logger.error('File set is not contiguous months')
    sys.exit(-2)
  data.fillna(0,inplace=True)
  logger.info('Data read for %d months'% len(months_12))
  return data

def to_quarters(df) -> pd.DataFrame:
  '''collapse the monthly series into quarters, returning a new dataframe'''
  qdf=pd.DataFrame(index=df.index)
  qs=[]
  for c in df.columns:
    q=1+((c%100)-1)//3
    qs+=[q+100*(c//100)]
  qm=pd.DataFrame(zip(df.columns,qs),columns=['month','quarter'])
  uq=pd.unique(qs)
  for qtr in uq:
    qcs=list(qm.loc[qm['quarter']==qtr,'month'])
    qdf[qtr]= df[qcs].astype(int).sum(axis=1)
  qdf['total']=qdf.sum(axis=1)
  qdf=qdf.loc[qdf.total != 0]
  return qdf


def geolocate(geocoder,country):
  '''function to get longitude and latitude data from country name
  args: geocoder - the function that makes the api call
    country a string of the country name
  returns pair of lat, long
  '''

  # Geolocate the center of the country
  special={}
  special['Georgia']={
    'country':'Georgia',
    'country_code':'ge'}
  special['Korea, Republic of']={
    'country':'Korea',
    'country_code':'kr'}
  special['Palestine, State of']={
    'country':'Palestine',
    'country_code':'ps'}
  special['Taiwan, Province of China']={
    'country':'Taiwan',
    'country_code':'tw'}
  if country in special:
    alt_info=special[country]
    loc=geocoder(alt_info['country'],country_codes=alt_info['country_code'])
  else:
    loc = geocoder(country)
    if loc is None:
      logger.error('Unable to geo-locate country: %s'%country)
      sys.exit(-3)
  # And return latitude and longitude
  return (loc.latitude, loc.longitude)

def popup_html(country,rw):
  # build a grid to handle starting not in 1st quarter
  grid=pd.DataFrame([],columns=['Q1','Q2','Q3','Q4'])
  for col in rw.index:
    if isinstance(col,int):
      y=col//100
      q='Q%d'% (col%100)
      grid.at[y,q]=rw[col]
  grid.fillna(0,inplace=True)
  grid['Year']=grid.sum(axis=1)
  grid=grid.astype(int)

  html = country + '<br><table style="height: 126px; width: 350px;"><tr>'
  for col in ['Year']+list(grid.columns):
    html+=f'<th>{col}</th>'
  for y,grw in grid.iterrows():
    for ix,col in enumerate(grid.columns):
      val= '{:,}'.format (grw[col])
      if ix >0:
        html+='<td>' + val + '</td>'
      else:
        yr='%d'%(y)
        html+='</tr><tr><td>'+yr+'</td><td>' + val + '</td>'
  html+='</tr></table>'
  return html

def create_chart(df):
  '''Create a world map to show distributions of provided counts '''

  world_map= folium.Map(tiles='cartodbpositron',legend_name='Test Legend')  #empty map
  marker_cluster = MarkerCluster().add_to(world_map)
  #for each coordinate, create circlemarker the right size
  for ix,rw in df.iterrows():
    lat = rw['lat']
    long = rw['long']
    radius=math.ceil(math.log(rw['total']))*8 # pixels logarithmic scaling
    popup_text=popup_html(ix,rw)
    folium.CircleMarker(location = [lat, long], radius=radius, popup= popup_text, fill =True).add_to(marker_cluster)
  return world_map

def lat_longs(geocoder,df):
  '''given a data frame with countries as the index, add columns for lat and long and save as a cache for next time
  args:
    geocoder - possibly with a rate limiter.
    data frame with countries as the index
  returns: modified dataframe now with 'lat' and 'long' columns
  '''
  cache_name='data/cache.json'
  try:
    with open (cache_name) as f:
      cache=json.load(f)
  except FileNotFoundError:
    cache={}
  df.lat=np.nan
  df.long=np.nan
  for ix,_ in df.iterrows():
    if ix in cache:
      lat_long=(cache[ix]['lat'],cache[ix]['long'])
      logger.debug(ix + ' cache hit')
    else:
      print(ix +' miss')
      lat_long=geolocate(geocoder,ix)
    df.loc[ix,'lat']=lat_long[0]
    df.loc[ix,'long']=lat_long[1]
  logger.info('All coordinates OK')
  df[['lat','long']].to_json(cache_name,orient='index')
  return df




def main():
  '''create the html page'''
  df=read_data()
  months=df.columns
  qdf=to_quarters(df)
  geolocator = Nominatim(user_agent='bok_country_chart')
  geocoder = rl.RateLimiter(geolocator.geocode, min_delay_seconds=1)

  df=lat_longs(geocoder,qdf)
  world_map=create_chart(df)
  #show the map
  # construct a file name
  out_file='data/bok_usage_chart_%d'% min(months)
  if min(months) != max(months):
    out_file=out_file+'_to_%d'% max(months)
  out_file=out_file+'.html'
  world_map.save(out_file)
  logger.info('saved to '+out_file)


if __name__=='__main__':
  main()
