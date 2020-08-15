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


water_data = pd.read_csv('Water_FINAL.csv')

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
        options = [{'label': huc, 'value': huc} for huc in water_data.groupby('HUC12_')['coordinates'].nunique().sort_values(ascending = False).index.tolist()]
    ),

    dcc.Dropdown(
        id = 'year_dropdown',
        # Get the HUC12s, sorted on the number of unique coordinates per HUC12
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




# # CALLBACK 1: Draws the map with layers based on the selected overlay variable, level (for multi-variables), 
# # and transformation
# @app.callback(
#     Output("map", "figure"),
#     [Input('df_store', 'data'),
#      Input("layer_opacity_slider", "value"),
#      Input("multi_variable_levels_dropdown", "value"),
#      Input('layer_checkbox', 'values'),
#      Input('transform_dropdown', 'value')],
#      [State('overlay_variable_dropdown', 'value')])
# def update_figure(df_store, layer_opacity_slider_value, multi_variable_levels_dropdown_value, layer_checkbox_value, 
# transform_dropdown_value, variable_dropdown_value):

#     #Load city data from df_store
#     city_data = json.loads(df_store)

#     #Create GDF with desired variable
#     gdf = prepare_gdf(city_data, variable_dropdown_value, multi_variable_levels_dropdown_value)

#     #Read what transformation the user is requesting
#     if transform_dropdown_value != 'Value':
#         if transform_dropdown_value == '% of Population':
#             population_gdf = prepare_gdf(city_data, 'population', None)
#             transformer_gdf = population_gdf.loc[:, ['zipcode', 'population']]
#             transformer_gdf['population'] = transformer_gdf['population'] / 100
#         elif transform_dropdown_value == 'Density (per square mile)':
#             land_area_gdf = prepare_gdf(city_data, 'land_area_in_sqmi', None)
#             transformer_gdf = land_area_gdf.loc[:, ['zipcode', 'land_area_in_sqmi']]
#         elif transform_dropdown_value == '% of Median Household Income':
#             household_income_gdf = prepare_gdf(city_data, 'median_household_income', None)
#             transformer_gdf = household_income_gdf.loc[:, ['zipcode', 'median_household_income']]
#             transformer_gdf['median_household_income'] = transformer_gdf['median_household_income'] / 100

#         transformer_gdf.columns = ['zipcode', 'transformer']

#         #Merge two dataframes
#         gdf = gdf.merge(transformer_gdf, on = 'zipcode', how = 'inner')
#         gdf[variable_dropdown_value] = gdf[variable_dropdown_value] / gdf['transformer']

#         #Drop transformer row from gdf
#         gdf = gdf.drop('transformer', axis = 1)
#         gdf = gdf.replace([np.inf, -np.inf], np.nan)
#         gdf = gdf.dropna()

#     #Get color map (based on variable selected in dropdown)
#     colors = set_overlay_colors(gdf[variable_dropdown_value])

#     #Set hover text (based on variable selected in dropdown)
#     gdf['hover_text'] = 'Zipcode: ' + gdf['zipcode'] + '<br /> ' + variable_dropdown_value + ': ' + round(gdf[variable_dropdown_value], 1).astype(str)


#     is_layer_visible = len(layer_checkbox_value) == 1

#     #Layers: District polygons, each with different colors defined by color map
#     layers=[{
#         'name': 'Population',
#         'sourcetype': 'geojson',
#         'visible': is_layer_visible,
#         'source': json.loads(gdf.loc[gdf.index == i, :].to_json()),
#         'type': 'fill',   
#         'color': colors[i],
#         'opacity': layer_opacity_slider_value
#         } for i in gdf.index]

    
#     data = [go.Scattermapbox(
#             lat=gdf['LAT'], 
#             lon=gdf['LON'], 
#             mode='markers', 
#             marker={'opacity': 0},
#             text=gdf['hover_text'], 
#             hoverinfo='text', 
#             name= 'Philadelphia Districts')]

#     return {"data": data,
#             "layout": go.Layout(
#                 autosize=True, 
#                 hovermode='closest', 
#                 showlegend=False, 
#                 height=700,
#                 mapbox={
#                     'accesstoken': mapbox_access_token, 
#                     'bearing': 0, 
#                     'layers': layers,
#                     'center': {'lat': gdf['LAT'][0], 'lon': gdf['LON'][0]}, 
#                     'pitch': 0, 'zoom': 10,
#                     "style": 'mapbox://styles/mapbox/streets-v10'
#                     }
#                 )
#             }


# #CALLBACK 2: For multi-variables, sets the dropdown options that allow user to choose which level to display the choropleth map for.
# @app.callback(
#     [Output("multi_variable_levels_dropdown", "options"),
#      Output("multi_variable_levels_dropdown", "value"),
#      Output("multi_variable_levels_dropdown", "style"),],
#     [Input('df_store', 'data'),
#     Input('overlay_variable_dropdown', 'value')])
# def set_levels_dropdown_options(df_store, variable_dropdown_value):

#     #Load city data
#     city_data = json.loads(df_store)

#     #Check whether single or multi variable
#     single_var, multi_var = sort_variables_by_type(city_data)

#     if variable_dropdown_value in multi_var:

#         levels = get_multi_var_levels(city_data, variable_dropdown_value)

#         options = [{'label': titlecase(e), 'value': e} for e in levels]
#         value = options[0]['value']
        
#         return options, value, {'display': 'block'}
    
#     else:
#         return [], [], {'display': 'none'}


if __name__ == '__main__':
    app.run_server(debug=False)