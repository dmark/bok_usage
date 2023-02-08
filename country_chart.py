#! /usr/bin/env python
'''Main program to create country chart based on usage data from Janeway'''

import json
import math

import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import geopy.extra.rate_limiter as rl
import numpy as np
import pandas as pd


def read_data():
  '''Read the data and summarizes into calendar quarters
  returns: a dataframe with quarter values with the country as index'''
  in_file='data/BoK-geographic-202003-202210.xlsx'
  df=pd.read_excel(in_file)
  df.fillna(0,inplace=True)
  df=df.set_index('Country')
  qdf=pd.DataFrame(index=df.index)
  qs=[]
  for c in df.columns:
    q=1+(c.month-1)//3
    qs+=[q+100*c.year]
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
  special=['Georgia','Korea, Republic of','Palestine, State of']
  if country=='Georgia':
    loc= geocoder(country,country_codes='ge')

  if country.startswith('Korea'):
    loc= geocoder('Korea',country_codes='kr')

  if country.startswith('Palestine'):
    loc= geocoder('Palestine',country_codes='ps')

  if country not in special:
    loc = geocoder(country)
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
      print(ix + ' hit')
    else:
      print(ix +' miss')
      lat_long=geolocate(geocoder,ix)
    df.loc[ix,'lat']=lat_long[0]
    df.loc[ix,'long']=lat_long[1]
  print('-')
  df[['lat','long']].to_json(cache_name,orient='index')
  return df




def main():
  '''create'''
  qdf=read_data()
  geolocator = Nominatim(user_agent='bok_country_chart')
  geocoder = rl.RateLimiter(geolocator.geocode, min_delay_seconds=1)

  df=lat_longs(geocoder,qdf)
  world_map=create_chart(df)
  #show the map
  out_file='data/bok_chart_2022_10.html'
  world_map.save(out_file)
  print('saved to '+out_file)


if __name__=='__main__':
  main()
