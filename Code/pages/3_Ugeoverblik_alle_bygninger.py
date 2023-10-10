import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import quote

from datetime import datetime
from datetime import timedelta
from tqdm import tqdm
from stqdm import stqdm
import ruptures as rpt
from urllib.parse import quote


from streamlit_functions import select_tree, getMeterPoints, getMeterReadings
from streamlit_tree_select import tree_select
import streamlit.components.v1 as components

import matplotlib.pyplot as plt

from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Grid, Line, Scatter, Sankey, WordCloud, HeatMap, Calendar, Sunburst, TreeMap
from streamlit_echarts import st_pyecharts

import locale
#for lang in locale.windows_locale.values():
#    st.write(lang)

locale.setlocale(locale.LC_ALL, "da_DK")

from os import listdir
from os.path import isfile, join

st.set_page_config(layout="wide", page_title="Individuel forbrug", page_icon="https://media.licdn.com/dms/image/C4E0BAQEwX9tzA6x8dw/company-logo_200_200/0/1642666749832?e=2147483647&v=beta&t=UiNzcE1RvJD3kHI218Al7omOzPLhHXXeE_svU4DIwEM")
st.sidebar.image('https://via.ritzau.dk/data/images/00181/e7ddd001-aee3-4801-845f-38483b42ba8b.png')
nodes = select_tree()
#st.write(nodes)
if not st.session_state.valgt_meter:
    st.warning('Vær sød at vælge en adresse ude i siden') 
    st.stop()
IDs = list(st.session_state.valgt_meter)
#st.write(IDs)

@st.cache_data
def meters_indi(): 
    df = pd.read_csv('https://github.com/Mikkel-schmidt/elfor/raw/master/Data/timeforbrug/' + quote(st.session_state.kunde[0]) + '.csv')
    #df = df[df['meter'].isin(list(st.session_state.valgt_meter))]
    return df

df = meters_indi() 

df['meter'] = pd.to_numeric(df['meter'])
df = df[df['Adresse'].isin(IDs)]
df['from'] = pd.to_datetime(df['from'], utc=True)
df['ugedag'] = df['from'].dt.day_name(locale='da_DK')

#st.write(df['meter'].unique().isin(list(st.session_state.valgt_meter)))


col1, col2 = st.columns([1,4])

col1.header('Ugeoverblik')


#@st.cache_resource
def heatmapp(df):
    dff = df.groupby([df['from'].dt.day_name(locale='da_DK'), df['from'].dt.hour]).agg({'amount': ['mean', 'std']}).reset_index(names=['day', 'hour'])
    dff.columns = ['_'.join(tup).rstrip('_') for tup in dff.columns.values]
    #st.write(dff)
    dff['day_'] = dff['day']
    dff['day_'].replace({
            "Mandag": 0,
            "Tirsdag": 1,
            "Onsdag": 2,
            "Torsdag": 3,
            "Fredag": 4,
            "Lørdag": 5,
            "Søndag": 6},
            inplace=True,)
    dff.sort_values(['day_', 'hour'], ascending=False, inplace=True)
    
    #col1.write(dff)
    dff['x-axis'] = dff.apply(lambda row: row['day'] + ' kl. ' + str(row['hour']), axis=1)

    pivot = dff.pivot_table(index='day', columns='hour', aggfunc='mean', values='amount_mean', sort=False)
    pivot = pivot.iloc[:, ::-1]
    #col1.write(pivot)

    x_axis = pivot.columns[:-1].tolist()
    y_axis = pivot.index.tolist()
    data = [[i, j, pivot.iloc[j,i].round(1)] for i in range(24) for j in range(7)]
    #st.write(pivot)

    b1 = (
        HeatMap()
        .add_xaxis(x_axis)
        .add_yaxis("Forbrug [kWh]", y_axis, list(data), label_opts=opts.LabelOpts(is_show=True, position="inside"))
        .set_global_opts(
            legend_opts=opts.LegendOpts(orient='vertical', pos_left="center", is_show=False),
            visualmap_opts=opts.VisualMapOpts(min_=0, max_=pivot.max().max(), is_calculable=True, orient="horizontal", pos_left="center"),
            title_opts=opts.TitleOpts(
            ),
            toolbox_opts=opts.ToolboxOpts(orient='vertical', is_show=False),
        )
        .set_series_opts(
        )
    )
    return b1

col1, col2 = st.columns([4,1])
col2.subheader('Heatmap og ugeprofil')
col2.markdown("""I figuren til venstre kan man se hvordan forbruget fordeler sig henover timerne på en uge.
Her burde man kunne se hvordan åbningstiderne i bygningen er og om bygningen lukkes ned udenfor åbningstid""")
col2.markdown('Tallet i midten er det gennemsnitlige forbrug i den time på den ugedag.')

if df['bkps'].iloc[-1] >= df['bkps'].max():
    df_opti = df[df['bkps']==df['bkps'].iloc[-1]].groupby('from').agg({'meter': 'mean', 'amount': 'sum', 'day-moment': 'first'}).reset_index()
else:
    df_opti = df[df['bkps']==df['bkps'].min()].groupby('from').agg({'meter': 'mean', 'amount': 'sum', 'day-moment': 'first'}).reset_index()

df_norm = df[df['bkps']==df['bkps'].iloc[-1]].groupby('from').agg({'meter': 'mean', 'amount': 'sum', 'day-moment': 'first'}).reset_index()

with col1:
    figure = heatmapp(df.iloc[-2159:])
    st_pyecharts(figure, height='400px', key='hej')

#@st.cache_data
def ugeprofil(df):
    dff = df.groupby([df['from'].dt.day_name(locale='da_DK'), df['from'].dt.hour]).agg({'amount': ['mean', 'std']}).reset_index(names=['day', 'hour'])
    dff.columns = ['_'.join(tup).rstrip('_') for tup in dff.columns.values]
    #st.write(dff)
    dff['day_'] = dff['day']
    dff['day_'].replace({
            "Mandag": 0,
            "Tirsdag": 1,
            "Onsdag": 2,
            "Torsdag": 3,
            "Fredag": 4,
            "Lørdag": 5,
            "Søndag": 6},
            inplace=True,)
    dff.sort_values(['day_', 'hour'], ascending=True, inplace=True)
    #st.write(dff)
    dff['x-axis'] = dff.apply(lambda row: row['day'] + ' kl. ' + str(row['hour']), axis=1)
    return dff



uge = ugeprofil(df_opti)
uge2 = ugeprofil(df_norm)

#st.write(uge2)

#st.write(ug)
#st.write(ug2)
ugg = uge[['day', 'hour', 'amount_mean', 'x-axis']].merge(uge2[['day', 'hour', 'amount_mean']], how='outer', on=['day', 'hour'], suffixes=('_opti', '_now'))
ugg['besparelse_kwh'] = ugg['amount_mean_now'] - ugg['amount_mean_opti']
st.write('Mulig besparelse på ' + str(ugg['besparelse_kwh'].sum()*52) + ' kWh')
st.write('Årlig forbrug på ' + str(ugg['amount_mean_now'].sum()*52) + ' kWh')
st.write('Mulig besparelse på ' + str((ugg['besparelse_kwh'].sum()*52)/(ugg['amount_mean_now'].sum()*52)*100) + '%')


 


