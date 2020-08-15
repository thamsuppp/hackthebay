import os
import dash
import us
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_table
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go

import json
import requests

#import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.colors as mcolors
import matplotlib.cm as cm

from datetime import datetime
from stringcase import titlecase

mapbox_access_token = "pk.eyJ1IjoidGhhbXN1cHBwIiwiYSI6ImNrN3Z4eTk2cTA3M2czbG5udDBtM29ubGIifQ.3UvulsJUb0FSLnAOkJiRiA"


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True
if 'DYNO' in os.environ:
    app_name = os.environ['DASH_APP_NAME']
else:
    app_name = 'dash-scattermapboxplot'

# Load the entire water data
water_data = pd.read_csv('Water_FINAL.csv')

# Round latitude and longitude to 3dp
water_data['Latitude'] = water_data['Latitude'].apply(lambda x: round(x, 3))
water_data['Longitude'] = water_data['Longitude'].apply(lambda x: round(x, 3))


print('Loaded')



### APP LAYOUT ###
app.layout = html.Div([
    html.Div([html.H1("Explore the Chesapeake Bay")],
             style={'textAlign': "center", "padding-bottom": "10", "padding-top": "10"}),


    dcc.Dropdown(
        id = 'parameter_dropdown',
        options = [{'label': param, 'value': param} for param in water_data['Parameter'].unique()] 
    ),

    dcc.Dropdown(
        id = 'aggregation_dropdown',
        options = [{'label': 'count', 'value': 'count'},
                    {'label': 'mean', 'value': 'mean'},
                    {'label': 'median', 'value': 'median'},
                    {'label': 'min', 'value': 'min'},
                    {'label': 'max', 'value': 'max'}
        ]
    ),

    dcc.Dropdown(
        id = 'huc_dropdown',
        # Give the dropdown values of HUCs in descending order of unique # of coordinates for that HUC
        options = [{'label': huc, 'value': huc} for huc in water_data.groupby('HUC12_')['coordinates'].nunique().sort_values(ascending = False).index.tolist()]
    ),

    dcc.Dropdown(
        id = 'year_dropdown',
        options = [{'label': year, 'value': year} for year in water_data['Year'].unique()]
    ),

    dcc.Dropdown(
        id = 'month_dropdown',
        options = [{'label': month, 'value': month} for month in range(1, 13)]
    ),

    html.Div(
        id = 'huc_div'
    ),


    html.Div(
        [   
            dash_table.DataTable(
                id='station_list',
                columns=[
                    {'id': 'Coordinates', 'name': 'Coordinates'},
                    {'id': 'HUC12', 'name': 'HUC12'},
                    {'id': 'HUC Name', 'name': 'HUC Name'},
                    {'id': 'County', 'name': 'County'},
                    {'id': 'State', 'name': 'State'},
                    {'id': 'Station', 'name': 'Station'},
                    {'id': 'Station Code', 'name': 'Station Code'}
                ],
                data = [],
                row_selectable='multi',
                row_deletable=True,
                selected_rows=[],
            ),
        ],
    ),

    dcc.Graph(id = 'graph'),
    
    html.Div(dcc.Graph(id="map")),
    dcc.Checklist(
        id = 'show_map_checklist',
        options = [{'label': 'Show Map', 'value': True}],
        value = [True])



], className="container")


### APP CALLBACKS ###


@app.callback(
    Output('huc_div', 'children'),
    [Input('huc_dropdown', 'value')]
)
def show_huc_name(huc):
    return water_data.loc[water_data['HUC12_'] == huc, 'HUCNAME_'].reset_index(drop = True)[0]


@app.callback(
    Output('station_list', 'data'),
    [Input('map', 'clickData')],
    [State('station_list', 'data')]
)
def update_station_list(click_data, datatable):

    print(click_data)
    longitude = click_data['points'][0]['lon']
    latitude = click_data['points'][0]['lat']

    longitude = round(longitude, 3)
    latitude = round(latitude, 3)

    station_info = water_data.loc[(water_data['Longitude'] == longitude) & (water_data['Latitude'] == latitude), 
                                ['coordinates', 'HUC12_', 'HUCNAME_', 'COUNTY_', 'STATE_', 'Station', 'StationCode', 'Latitude', 'Longitude']]
    print(station_info)
    station_info = station_info.reset_index(drop = True).iloc[0, :]

    data = {'Coordinates': station_info['coordinates'],
            'HUC12': station_info['HUC12_'],
            'HUC Name': station_info['HUCNAME_'],
            'County': station_info['COUNTY_'],
            'State': station_info['STATE_'],
            'Station': station_info['Station'],
            'Station Code': station_info['StationCode'],
            'Latitude': station_info['Latitude'],
            'Longitude': station_info['Longitude']}

    datatable.append(data)

    return datatable




@app.callback(
    Output('graph', 'figure'),
    [Input('parameter_dropdown', 'value'),
    Input('station_list', 'data'),
    Input('station_list', 'selected_rows')]
)
def draw_graph(parameter, datatable, datatable_selected_rows):


    data_selected = [datatable[index] for index in datatable_selected_rows]

    coordinates_selected = [(e['Latitude'], e['Longitude']) for e in data_selected]

    fig = go.Figure()

    for station_coords in coordinates_selected:

        # Subset by measure value
        measure = water_data.loc[(water_data['Longitude'] == station_coords[1]) & (water_data['Latitude'] == station_coords[0]) & 
                                (water_data['Parameter'] == parameter), ['Date', 'Time', 'MeasureValue']]
        # Change to datetime object
        measure['Date'] = measure['Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
        measure = measure.sort_values('Date', ascending = True)
        measure['hoverinfo'] = measure.apply(lambda row: '{}, {}'.format(datetime.strftime(row['Date'], '%Y-%m-%d'), row['Time']), axis = 1)


        fig.add_trace(
            go.Scatter(
                x = measure['Date'],
                y = measure['MeasureValue'],
                name = '{}, {}'.format(station_coords[0], station_coords[1]),
                mode = 'lines',
                text = measure['hoverinfo'],
                hoverinfo = 'text+y'
            ))

    fig.update_layout(
        title = parameter,
        legend = dict(x = -.1, y = 1.2),
        yaxis_title = parameter,
        xaxis_title = 'Date'
    )

    return fig








@app.callback(
    Output('map', 'figure'),
    [Input('show_map_checklist', 'value'),
    Input('huc_dropdown', 'value'),
    Input('parameter_dropdown', 'value'),
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('aggregation_dropdown', 'value')]
)
def show_map(show_map_checklist_value, huc, parameter, year, month, aggregation):


    # Subset by HUC
    water_data_subset = water_data.loc[water_data['HUC12_'] == huc, :]

    # Choose the aggregation
    if aggregation == 'count':
        param_summary = water_data_subset.loc[(water_data_subset['Year'] == year) & (water_data_subset['Month'] == month) & (water_data_subset['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].count()
    elif aggregation == 'mean':
        param_summary = water_data_subset.loc[(water_data_subset['Year'] == year) & (water_data_subset['Month'] == month) & (water_data_subset['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].mean()
    elif aggregation == 'median':
        param_summary = water_data_subset.loc[(water_data_subset['Year'] == year) & (water_data_subset['Month'] == month) & (water_data_subset['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].median()
    elif aggregation == 'min':
        param_summary = water_data_subset.loc[(water_data_subset['Year'] == year) & (water_data_subset['Month'] == month) & (water_data_subset['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].min()
    elif aggregation == 'max':
        param_summary = water_data_subset.loc[(water_data_subset['Year'] == year) & (water_data_subset['Month'] == month) & (water_data_subset['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].max()
    else:
        param_summary = water_data_subset.loc[(water_data_subset['Year'] == 2015) & (water_data_subset['Month'] == 1) & (water_data_subset['Parameter'] == 'TN'), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].mean()
        
    data = [go.Scattermapbox(
            lat = param_summary['Latitude'],
            lon = param_summary['Longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size = 7,
                color = param_summary['MeasureValue'],
                colorscale = 'Bluered',
                #cmin = water_data_subset.loc[water_data_subset['Parameter'] == parameter, 'MeasureValue'].min(),
                #cmax = water_data_subset.loc[water_data_subset['Parameter'] == parameter, 'MeasureValue'].max()
            ),
            text= param_summary['MeasureValue'],
        )]

    return {'data': data,
            'layout': go.Layout(
                height = 800,
                width = 1000,
                margin = {'l': 50, 'r': 50, 't': 0, 'b': 0},
                hovermode='closest',
                showlegend = True,
                mapbox=dict(
                    accesstoken=mapbox_access_token,
                    bearing=0,
                    center=go.layout.mapbox.Center(
                        lat=39,
                        lon=-76.4
                    ),
                    pitch=0,
                    zoom=9
                )
            )
    }



if __name__ == '__main__':
    app.run_server(debug=False)