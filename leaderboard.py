'''grab the to n all time countries'''

from country_chart import read_data
lb_file='data/leader_board.xlsx'
qdf=read_data()
qdf['Total']=qdf.sum(axis=1)
qdf.sort_values(by='total',ascending=False,inplace=True)
print(qdf[['total']].head(12))
print(qdf.shape[0])
qdf.to_excel(lb_file)
print('Wrote ' + lb_file)