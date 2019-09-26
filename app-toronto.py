#assumption: packages already installed:
#plotly==2.5.1
#dash==0.21.0
#dash_core_components==0.22.1
#dash-html-components==0.10.0
#dash-renderer==0.12.1


#IMPORT THE LIBRARIES
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import das_table_experience as dt
#numpy, pandas and csv libraries
import csv
import pandas as pd
import numpy as np
from pandas.plotting import radviz
#BeautifulSoup to scrape the web and lxml for the html parser:
from bs4 import BeautifulSoup
import requests
import lxml
import json
#For clustering
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn import metrics
from scipy.spatial.distance import cdist
#To get the longitude and latitude values
import pgeocode
from geopy.geocoders import Nominatim
#Matplotlib
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt
#for plot.ly visuals
import plotly.io as pio
import plotly.graph_objs as go
import plotly.express as px
import plotly.figure_factory as ff
import math
#chart studio
from chart_studio.grid_objs import Grid, Column
from plotly.tools import FigureFactory as FF
import time
import chart_studio.plotly as py
from chart_studio.plotly import plot, iplot
#plotnine
rom plotnine import *
from plotnine.data import *

from string import ascii_letters
#To render the map
import folium
import branca
from folium import plugins
from folium.plugins import HeatMap
from folium.plugins import Fullscreen
import os
from ipywidgets import interact


#mapbox credentials
mapbox_access_token = 'pk.eyJ1IjoiZGlucmVnaW5hIiwiYSI6ImNrMHkzOXNyZzBjYnUzbXJ5bmkzMHAwcG8ifQ.up4c0fEdddwiBhOfbKHBzA'


#CONNECT TO HEROKU
import psycopg2
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')


#LAUNCH THE DASH APPLICATION
appToronto = dash.Dash()
#appToronto = dash.Dash(_name_)
#Flask app
#server = appToronto.server

#DATA
#import data
plotBubbleDF = pd.read_csv('plotBubbleDF.csv')
th = pd.read_csv('plotBubbleDF.csv')
#dropdown data
dashDF = th.drop(columns=['area', 'dwelling', 'lat', 'long', 'size'])
data = px.scatter(plotBubbleDF)
hovertextDF = plotBubbleDF.drop(columns=['long', 'lat'])
bubbleSizeDF = hovertextDF.sort_values(['borough', 'neighborhood'])


#OPTIONS FOR THE DASHBOARD
#DROPDOWN OPTIONS
#will make another plot that will change according to the given option
#options need to be in the form of a dictionary
#options --> columns only with continuous variables from nth column to nth column
dropFeatures = th.columns[1:-1]
opts = [{'label' : i, 'value' : i} for i in dropFeatures]

#SLIDER OPTIONS
#range slider to filter the plot and update the view with the given price range
#need to make a mark dictionary --> the ticks on the slider our ticks are based on home values
#used binning to bin the prices. we'll use the bins as the tick intervals. there are 26 bins, so we have 26 marks.

sliderBins = ['200k -250k', '250k-300k', '300k-325k', 
              '325k-350k', '350k-375k', '375k-400k', 
              '400k-425k', '425k-450k', '450k-475k', 
              '465k-500k', '500k-525k', '525k-550k', 
              '550k-575k', '575k-600k', '600k-625k', 
              '625k-650k', '650k-675k', '675k-700k', 
              '700k-750k', '750k-800k', '800k-850k', 
              '850k-900k', '900k-1M', '1M-1.5M', 
              '1.5M-2M', '2M+']
binMark = {i : sliderBins[i] for i in range (0, 26)}

#TEXT OPTIONS
#text for the hover label
hover_text = []
bubble_size = []

for index, row in hovertextDF.iterrows():
    hover_text.append(('Neighborhood: {neighborhood}'+ ' Area: {area}<br>'+
                      'Score: {value}' + 
                       ' Grade: {grade}<br>' + 
                       'Average Home Value: ${dwelling}'+'0').format(neighborhood=row['neighborhood'],
                                                    area=row['area'],
                                                      value = row['overall'],
                                                     grade=row['grade'],
                                                     dwelling=row['dwelling'],
                                                     ))
    bubble_size.append(row['size'])
    #bubble_size.append(math.sqrt(row['size']))
    
hovertextDF['text'] = hover_text
hovertextDF['size'] = bubble_size
sizeref = 2.*max(hovertextDF['size'])/(100**2)

#dictionary with dataframes for each borough:
boroughNames = ['Scarborough', 
                'Etobicoke', 
                'York', 
                'North York', 
                'Downtown Toronto', 
                'East Toronto', 
                'West Toronto', 'Central Toronto', 'East York']
boroughData = {borough:hovertextDF.query("borough == '%s'" %borough)
              for borough in boroughNames}


#CREATE A FIGURE
fig = go.Figure()

for boroughName, borough in boroughData.items():
    #fig.add_trace(go.Scatter(
    trace_1 = go.Scatter(x= borough['dwelling'], 
                         y = borough['overall'],
                         name=boroughName, 
                         text=borough['text'],
                         marker_size=borough['size'],)
#marker appearance and layout
fig.update_traces(mode='markers', 
                  marker =dict(opacity = 0.2, 
                               sizemode='area', 
                               sizeref=sizeref, 
                               line_width=2))

fig.update_layout(title='Neighborhood Scores',
                  xaxis=dict(title='Rating',
                             gridcolor='white',
                             type='log',
                             gridwidth=2,),
                  yaxis=dict(title='Score',
                             gridcolor='white',
                             gridwidth=2,),
                  paper_bgcolor='rgb(243, 243, 243)',
                  plot_bgcolor='rgb(243, 243, 243)',)

fig = go.Figure(data = [trace_1], layout = layout)



##CREATE A DASH LAYOUT
#1. make a division then bring the plot inside
#2. id --> the name of our component. so we can call it by its name
#save script and import on terminal
appToronto.layout = html.Div([
  #adding a header
  html.Div([
    html.H1("Toronto Neighborhoods: Report Cards are in!"),
    html.P("How do the neighborhoods of Toronto measure up? We analyzed characteristics and profiles of the 140 neighborhoods across the Toronto boroughs.")],
    style = {'padding' : '50px',
             'backgroundColor' : '#000000'}),
  #adding a plot
  dcc.Graph(id='plot', figure = fig),
  #adding dropdown
  html.P([
    html.Label("Select a Feature"),
    dcc.Dropdown(id='opt',
                 options = opts,
                 value = opts[0])
      ], style = {'width' : '400px',
                  'fontSize' : '20px',
                  'padding-left' : '100px',
                  'display' : 'inline-block'})
  #placing the slider on the plot
  #min is the minimum value of the slider. our bins begin at $200k, so we'll set 200000 as the min and 3000000 as the max
  #value is the default value of the slider. 
      #--> this is different from the dropdown component
      # --> range slider component takes in 2 values in a list
      #--> 2 input values are taken in: start value (X[0]) and end value (X[1])
  html.P([
    html.Lable("Price Range"),
    dcc.RangeSlider(id = 'sliderBin',
                    marks = binMark,
                    min = 200000,
                    max = 3000000,
                    value = [1, 24])
      ], style = {'width' : '80%',
                 'fontSize' : '20px',
                 'padding-left' : '100px',
                 'display' : 'inline-block'})
])


#ADD THE CALLBACK FUNCTIONS
#make a connection between input data (dropdown component, named opt) and output data (graph component named plot)
#connection is made by adding a callback function 
  #--> function executed later when it gets the real execution command 
  # --> usually used for updating
  #--> callbacks are slackers : do their work not when they get the command, do the work after the other command lines are executed and we call them back again
#making this connection will update the graph by the dropdown selection
#callback for slider and callback for dropdown
@appToronto.callback(Output('plot', 'figure'),
                    [Input('opt', 'value'),
                    Input('slider', 'value')])

#CALLBACK FUNCTION TO UPDATE THE FIGURE
#update function to take input data and return output
#input data = name of the feature variable selected
#shown as the -axis of the plot
def updateFigure(input1, input2):
  #filter data
  th2 = th[(th.dwelling_bins > sliderBins[input2[0]]) & (th.dwelling_bins < sliderBins[input2[1]])]
  #fig.add_trace(go.Scatter(
  #update the plot
  trace_1 = go.Scatter(x= th2.dwelling_bins, 
                      y = th2['overall'],
                      name = input1,
                      #text=borough['text'],
                      marker_size=th2['size'],)
  trace_2 = (go.Scatter(x= borough['dwelling_bins'], 
                      y = th2['overall'],
                      name = input1, 
                      #text=borough['text'],
                      marker_size=borough['size'],))
  fig = go.Figure(data = [trace_1, trace_2], layout = layout)
  return fig


## ADD THER SERVER CLAUSE
#name the server clause
#set debug = true so we can change and update while the server is running
if_name_ == '_main_':
    appToronto.run_server(debug= True)