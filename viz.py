import os
import dash
import us
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
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


water_data = pd.read_csv('water_subset.csv')
water_site_counts = water_data.groupby('coordinates')['coordinates'].agg(['count', 'first'])
water_site_counts['Lat'] = water_site_counts['first'].apply(lambda x: float(x[1:-1].split(', ')[1]))
water_site_counts['Long'] = water_site_counts['first'].apply(lambda x: float(x[1:-1].split(', ')[0]))



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
        id = 'year_dropdown',
        options = [{'label': year, 'value': year} for year in water_data['Year'].unique()]
    ),

    dcc.Dropdown(
        id = 'month_dropdown',
        options = [{'label': month, 'value': month} for month in range(1, 13)]
    ),

    
    html.Div(dcc.Graph(id="map")),
    dcc.Checklist(
        id = 'show_map_checklist',
        options = [{'label': 'Show Map', 'value': True}],
        value = [True])



], className="container")




    # html.Div([
    #     dcc.Input(id = 'city_search_input', placeholder = 'Search US city...'),
    #     html.Button('Search', id = 'city_search_button'),
    #     html.Div(children = 'Philadelphia', id = 'city_div'),
    #     dcc.Store('df_store')
    # ]),
    # html.H2('Overlay Options'),
    # dcc.Dropdown(id = 'overlay_variable_dropdown', options = overlay_variables, value = 'population'),
    # dcc.Dropdown(id = 'multi_variable_levels_dropdown', options = []),
    # dcc.Dropdown(
    #     id = 'transform_dropdown',
    #     options = [
    #         {'label': 'Value', 'value': 'Value'},
    #         {'label': '% of Population', 'value': '% of Population'},
    #         {'label': 'Density (per square mile)', 'value': 'Density (per square mile)'},
    #         {'label': '% of Median Household Income', 'value' : '% of Median Household Income'}],
    #     value = 'Value'
    #     ),
    # dcc.Checklist(
    #     id = 'layer_checkbox',
    #     options = [{'label': 'Show Overlay', 'value': True}],
    #     values = [True]
    # ),
    # html.Div(children = 'Opacity'),
    # dcc.Slider(id = 'layer_opacity_slider', min = 0, max = 1, step = 0.1, value = 0.8),


### APP CALLBACKS ###






@app.callback(
    Output('map', 'figure'),
    [Input('show_map_checklist', 'value'),
    Input('parameter_dropdown', 'value'),
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('aggregation_dropdown', 'value')]
)
def show_map(show_map_checklist_value, parameter, year, month, aggregation):

    if aggregation == 'count':
        param_summary = water_data.loc[(water_data['Year'] == year) & (water_data['Month'] == month) & (water_data['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].count()
    elif aggregation == 'mean':
        param_summary = water_data.loc[(water_data['Year'] == year) & (water_data['Month'] == month) & (water_data['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].mean()
    elif aggregation == 'median':
        param_summary = water_data.loc[(water_data['Year'] == year) & (water_data['Month'] == month) & (water_data['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].median()
    elif aggregation == 'min':
        param_summary = water_data.loc[(water_data['Year'] == year) & (water_data['Month'] == month) & (water_data['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].min()
    elif aggregation == 'max':
        param_summary = water_data.loc[(water_data['Year'] == year) & (water_data['Month'] == month) & (water_data['Parameter'] == parameter), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].max()
    else:
        param_summary = water_data.loc[(water_data['Year'] == 2015) & (water_data['Month'] == 1) & (water_data['Parameter'] == 'TN'), :].groupby('coordinates')[['MeasureValue', 'Longitude', 'Latitude']].mean()
        
    data = [go.Scattermapbox(
            lat = param_summary['Latitude'],
            lon = param_summary['Longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size = 7,
                color = param_summary['MeasureValue'],
                colorscale = 'Bluered',
                cmin = water_data.loc[water_data['Parameter'] == parameter, 'MeasureValue'].min(),
                cmax = water_data.loc[water_data['Parameter'] == parameter, 'MeasureValue'].max()
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
                    zoom=8
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