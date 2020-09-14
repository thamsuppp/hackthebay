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

import matplotlib.colors as mcolors
import matplotlib.cm as cm
import networkx as nx
#Set overlay colors for data
def set_overlay_colors(dataset):
    """Create overlay colors based on values
    :param dataset: gpd.Series, array of values to map colors to
    :returns: dict, hex color value for each language or index value
    """
    minima = dataset.min()
    maxima = dataset.max()
    #norm is the normalized color scale
    norm = mcolors.Normalize(vmin=minima, vmax=maxima, clip=True)
    #mapper object
    mapper = cm.ScalarMappable(norm=norm, cmap= 'PuBu')
    #mapper object maps every value in dataset to color
    colors = [mcolors.to_hex(mapper.to_rgba(v)) for v in dataset]
    #Dictionary of index:color mapping
    overlay_color = {
        idx: shade
        for idx, shade in zip(dataset.index, colors)
    }

    return overlay_color

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
water_part1 = pd.read_csv('water_condensed1.csv')
water_part2 = pd.read_csv('water_condensed2.csv')
water_part3 = pd.read_csv('water_condensed3.csv')
water_data = pd.concat([water_part1, water_part2, water_part3], axis = 0).reset_index(drop = True)



# Round latitude and longitude to 3dp
water_data['Latitude'] = water_data['Latitude'].apply(lambda x: round(x, 3))
water_data['Longitude'] = water_data['Longitude'].apply(lambda x: round(x, 3))

# Load Point Source Pollution Data
ps_data = pd.read_csv('PointSourceLoadDataState_updated.csv')
ps_data['LATITUDE'] = ps_data['LATITUDE'].apply(lambda x: round(x, 3))
ps_data['LONGITUDE'] = ps_data['LONGITUDE'].apply(lambda x: round(x, 3))
ps_data['Date'] = ps_data['DMR_DATE'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y'))
ps_data['Month'] = ps_data['Date'].dt.to_period('M')

# Load Relevant HUCs Data
huc_ps_data = pd.read_csv('HUCS_with_ps.csv')
# Have to convert to str as it is automatically saved as an int
huc_ps_data[['HUC12', 'TOHUC']] = huc_ps_data[['HUC12', 'TOHUC']].astype(str)
huc_ps_data['text'] = huc_ps_data.apply(lambda row: '{} -> {}'.format(row['HUC12'], row['TOHUC']), axis = 1)

print('Loaded')

### APP LAYOUT ###
app.layout = html.Div([
    html.Div([html.H1("Explore the Chesapeake Bay")],
             style={'textAlign': "center", "padding-bottom": "10", "padding-top": "10"}),


    dcc.Dropdown(
        id = 'parameter_dropdown',
        options = [{'label': param, 'value': param} for param in water_data['Parameter'].unique()] ,
        placeholder = 'Choose parameter'
    ),

    dcc.Dropdown(
        id = 'aggregation_dropdown',
        options = [{'label': 'count', 'value': 'count'},
                    {'label': 'mean', 'value': 'mean'},
                    {'label': 'median', 'value': 'median'},
                    {'label': 'min', 'value': 'min'},
                    {'label': 'max', 'value': 'max'}
        ],
        placeholder = 'Choose aggregation'
    ),

    dcc.Dropdown(
        id = 'huc_dropdown',
        # Give the dropdown values of HUCs in descending order of unique # of coordinates for that HUC
        options = [{'label': huc, 'value': huc} for huc in water_data.groupby('HUC12_')['coordinates'].nunique().sort_values(ascending = False).index.tolist()],
        placeholder = 'Choose HUC'
    ),

    dcc.Dropdown(
        id = 'year_dropdown',
        options = [{'label': year, 'value': year} for year in sorted(water_data['Year'].unique())],
        placeholder = 'Choose year'
    ),

    dcc.Dropdown(
        id = 'month_dropdown',
        options = [{'label': month, 'value': month} for month in range(1, 13)],
        placeholder = 'Choose month'
    ),

    html.Div(
        id = 'huc_div'
    ),


    html.Div(
        [   
            dash_table.DataTable(
                id='station_list',
                columns=[
                    {'id': 'Point Type', 'name': 'Point Type'},
                    {'id': 'Coordinates', 'name': 'Coordinates'},
                    {'id': 'Parameter', 'name': 'Parameter', 'presentation': 'dropdown'},
                    {'id': 'HUC12', 'name': 'HUC12'},
                    {'id': 'HUC Name', 'name': 'HUC Name'},
                    {'id': 'County', 'name': 'County'},
                    {'id': 'State', 'name': 'State'},
                    {'id': 'Station', 'name': 'Station'},
                    {'id': 'Station Code', 'name': 'Station Code'},
                    {'id': 'Facility', 'name': 'Facility'},
                    {'id': 'Discharge Type', 'name': 'Discharge Type'},
                ],
                data = [
                ],
                dropdown_conditional = [
                ],
                editable = True,
                row_selectable='multi',
                row_deletable=True,
                selected_rows=[],
            ),
        ],
    ),

    dcc.Graph(id = 'graph'),

    # html.H3('Time Series Predictions'),
    # dcc.Dropdown(
    #     id = 'plot_to_do_ts_dropdown',
    #     options = []
    # ),
    # dcc.Dropdown(
    #     id = 'ts_model_dropdown',
    #     options = [{'label': i, 'value': i} for i in ['Seasonal ARIMA', 'Seasonal ARIMA with Exogenous Predictors (SARIMAX)']]
    # ),
    # dcc.Dropdown(
    #     id = 'holdout_period_dropdown',
    #     options = []
    # ),
    
    dcc.Checklist(
        id = 'point_source_checklist',
        options = [{'label': 'Show Point Sources of Pollution', 'value': True}],
        value = [True]),
    
    html.Div(dcc.Graph(id="map")),

    html.H3('HUC Options'),
    dcc.Dropdown(
        id = 'huc_month_dropdown',
        options = [{'label': month, 'value': month} for month in ps_data['Month'].astype(str).unique()],
        placeholder = 'Select year and month'
    ),
    dcc.Checklist(
        id = 'show_huc_checklist',
        options = [{'label': 'Show HUC', 'value': True}],
        value = [True]),
    dcc.Dropdown(
        id = 'huc_parameter_dropdown',
        options = [{'label': i, 'value': i} for i in 
                    ['Nitrogen Load', 'Phosphorous Load', 'BOD5', 'TON', 'FLOW', 'TN', 'NH3', 'PO4', 'TOP', 'TP', 'TSS',
       'DO', 'NO23', 'Total Upstream Point Sources', 'Total Upstream TN', 'Total Upstream TP']
                    ],
        placeholder = 'Select parameter'
    )
], className="container")


### APP CALLBACKS ###


@app.callback(
    Output('huc_div', 'children'),
    [Input('huc_dropdown', 'value')]
)
def show_huc_name(huc):
    return water_data.loc[water_data['HUC12_'] == huc, 'HUCNAME_'].reset_index(drop = True)[0]


@app.callback(
    [Output('station_list', 'data'),
     Output('station_list', 'dropdown_conditional')],
    [Input('map', 'clickData')],
    [State('station_list', 'data'),
    State('station_list', 'dropdown_conditional')]
)
def update_station_list(click_data, datatable, datatable_dropdown_conditional):

    print(click_data)
    # Check if the clicked point is a point source or a station
    

    longitude = click_data['points'][0]['lon']
    latitude = click_data['points'][0]['lat']

    longitude = round(longitude, 3)
    latitude = round(latitude, 3)

    if click_data['points'][0]['curveNumber'] == 0: # Station:

        station_info = water_data.loc[(water_data['Longitude'] == longitude) & (water_data['Latitude'] == latitude), 
                                    ['coordinates', 'HUC12_', 'HUCNAME_', 'COUNTY_', 'STATE_', 'Latitude', 'Longitude', 'Parameter']]
        print(station_info)
        station_info_first = station_info.reset_index(drop = True).iloc[0, :]

        data = {
            'Point Type': 'Station',
            'Coordinates': station_info_first['coordinates'],
            'HUC12': station_info_first['HUC12_'],
            'HUC Name': station_info_first['HUCNAME_'],
            'County': station_info_first['COUNTY_'],
            'State': station_info_first['STATE_'],
            'Latitude': station_info_first['Latitude'],
            'Longitude': station_info_first['Longitude']}

        # Add the parameter dropdown options for this point
        dropdown_dict = {
            'if': {
                'column_id': 'Parameter',
                'filter_query': '{Coordinates} eq "' + str(station_info_first['coordinates']) + '"'
            },
            'options': [
                {'label': i, 'value': i} for i in station_info['Parameter'].unique()
            ]
        }


    elif click_data['points'][0]['curveNumber'] == 1: # Point Source:

        ps_info = ps_data.loc[(ps_data['LONGITUDE'] == longitude) & (ps_data['LATITUDE'] == latitude),
                            ['LONGITUDE', 'LATITUDE', 'FACILITY', 'DISCHARGE_TYPE', 'COUNTY_CITY', 'STATE', 'PARAMETER']]    
        
        ps_info_first = ps_info.reset_index(drop = True).iloc[0, :]

        print(ps_info_first)

        ps_coordinate = '{}, {}'.format(ps_info_first['LATITUDE'], ps_info_first['LONGITUDE'])

        data = {
            'Point Type': 'Point Source',
            'Coordinates': ps_coordinate,
            'County': ps_info_first['COUNTY_CITY'],
            'State': ps_info_first['STATE'],
            'Facility': ps_info_first['FACILITY'],
            'Discharge Type': ps_info_first['DISCHARGE_TYPE'],
            'Latitude': ps_info_first['LATITUDE'],
            'Longitude': ps_info_first['LONGITUDE']}

        # Add the parameter dropdown options for this point
        dropdown_dict = {
            'if': {
                'column_id': 'Parameter',
                'filter_query': '{Coordinates} eq "' + ps_coordinate + '"'
            },
            'options': [
                {'label': i, 'value': i} for i in ps_info['PARAMETER'].unique()
            ]
        }

    datatable.append(data)
    if not datatable_dropdown_conditional:
        datatable_dropdown_conditional = [dropdown_dict]
    else:
        datatable_dropdown_conditional.append(dropdown_dict)

    return datatable, datatable_dropdown_conditional


# @app.callback(
#     Output('plot_to_do_ts_dropdown', 'options'),
#     [Input('station_list', 'data'),
#     Input('station_list', 'selected_rows')]
# )
# def set_plot_to_do_ts_dropdown_options(datatable, datatable_selected_rows):

#     data_selected = [datatable[index] for index in datatable_selected_rows]
#     options = ['{}, {}'.format(e['Coordinates'], e['Parameter']) for e in data_selected]
#     options = [{'label': e, 'value': e} for e in options]

#     return options

# @app.callback(
#    Output('plot_to_do_ts_dropdown', 'options'),
#    [Input('plot_to_do_ts_dropdown', 'value'),
#    Input('ts_model_dropdown', 'value')]
# )
# def plot_ts_predictions(plot_dropdown_value, ts_model_dropdown_valu):

#     coords = (float(plot_dropdown_value.split(', ')[0]), float(plot_dropdown_value.split(', ')[1])
#     water_point = water.loc[(water['Latitude'] == coords[0]) & (water['Longitude'] == coords[1]), :]


@app.callback(
    Output('graph', 'figure'),
    [Input('station_list', 'data'),
    Input('station_list', 'selected_rows')]
)
def draw_graph(datatable, datatable_selected_rows):


    data_selected = [datatable[index] for index in datatable_selected_rows]

    fig = go.Figure()

    for station in data_selected:
        
        station_coords = (station['Latitude'], station['Longitude'])
        if station['Point Type'] == 'Station':

            # Subset by measure value - now graphs the parameter that is selected in the Parameter dropdown for that row
            measure = water_data.loc[(water_data['Longitude'] == station_coords[1]) & (water_data['Latitude'] == station_coords[0]) & 
                                    (water_data['Parameter'] == station['Parameter']), ['Date', 'Time', 'MeasureValue']]
            # Change to datetime object
            measure['Date'] = measure['Date'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
            measure = measure.sort_values('Date', ascending = True)
            measure['hoverinfo'] = measure.apply(lambda row: '{}, {}'.format(datetime.strftime(row['Date'], '%Y-%m-%d'), row['Time']), axis = 1)


            fig.add_trace(
                go.Scatter(
                    x = measure['Date'],
                    y = measure['MeasureValue'],
                    name = '{}, {}, {}'.format(station_coords[0], station_coords[1], station['Parameter']),
                    mode = 'lines',
                    text = measure['hoverinfo'],
                    hoverinfo = 'text+y'
                ))

        elif station['Point Type'] == 'Point Source':

            measure = ps_data.loc[(ps_data['LONGITUDE'] == station_coords[1]) & (ps_data['LATITUDE'] == station_coords[0]) & 
            (ps_data['PARAMETER'] == station['Parameter']), ['Date', 'VALUE', 'UNITS']]
            
            
            measure = measure.sort_values('Date', ascending = True)
            measure['hoverinfo'] = measure.apply(lambda row: datetime.strftime(row['Date'], '%Y-%m-%d'), axis = 1)

            fig.add_trace(
                go.Scatter(
                    x = measure['Date'],
                    y = measure['VALUE'],
                    name = '{}, {}, {}, {}'.format(station_coords[0], station_coords[1], station['Parameter'], measure['UNITS'].unique()[0]),
                    mode = 'lines',
                    text = measure['hoverinfo'],
                    hoverinfo = 'text+y'
                ))

    fig.update_layout(
        title = 'Station & Point Source Parameter Values',
        legend = dict(x = -.1, y = 1.2),
        yaxis_title = 'Value',
        xaxis_title = 'Date'
    )

    return fig

# For each facility, calculate the nutrient load for each month
def get_load_data(parameter):

    ps_data_params = ps_data.loc[(ps_data['PARAMETER'] == parameter) | (ps_data['PARAMETER'] == 'FLOW'), ['FACILITY', 'HUC', 'Month', 'PARAMETER', 'VALUE']] \
        .drop_duplicates(subset = ['FACILITY', 'HUC', 'Month', 'PARAMETER']) \
        .pivot(index = ['FACILITY', 'HUC', 'Month'], columns = 'PARAMETER', values = 'VALUE') \
        .reset_index()

    ps_data_params['LOAD'] = ps_data_params['FLOW'] * ps_data_params[parameter] * 80 * 8.344

    # Group by HUC and find total nutrient load for each month
    month_data_huc = ps_data_params.groupby(['HUC', 'Month'])['LOAD'].sum().reset_index()

    # Reshape to get monthly nutrient load for each HUC
    month_data_huc_pivot = month_data_huc.pivot(columns = 'HUC', index = 'Month', values = 'LOAD').fillna(0)
    
    return month_data_huc_pivot

@app.callback(
    Output('map', 'figure'),
    [Input('huc_dropdown', 'value'),
    Input('parameter_dropdown', 'value'),
    Input('year_dropdown', 'value'),
    Input('month_dropdown', 'value'),
    Input('huc_month_dropdown', 'value'),
    Input('huc_parameter_dropdown', 'value'),
    Input('aggregation_dropdown', 'value'),
    Input('point_source_checklist', 'value'),
    Input('show_huc_checklist', 'value')]
)
def show_map(huc, parameter, year, month, huc_month, huc_parameter, 
    aggregation, point_source_checklist_value, show_huc_checklist_value):

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
                size = 10,
                color = param_summary['MeasureValue'],
                colorscale = 'Bluered',
                #cmin = water_data_subset.loc[water_data_subset['Parameter'] == parameter, 'MeasureValue'].min(),
                #cmax = water_data_subset.loc[water_data_subset['Parameter'] == parameter, 'MeasureValue'].max()
            ),
            text= param_summary['MeasureValue'],
            name = 'Stations'
        )]

    point_sources = go.Scattermapbox(
        lat = ps_data['LATITUDE'],
        lon = ps_data['LONGITUDE'],
        mode = 'markers',
        marker = go.scattermapbox.Marker(
                size = 5,
                color = 'red'
        ),
        text = ps_data['FACILITY'],
        name = 'Point Sources'
    )

    if point_source_checklist_value == [True]:
        data.append(point_sources)

    if show_huc_checklist_value == [True]:
        print('Plotting HUCs')
        huc_data = huc_ps_data.copy()

        if huc_parameter in ['Total Upstream Point Sources', 'Total Upstream TN', 'Total Upstream TP']:

            if huc_parameter == 'Total Upstream Point Sources':
                
                # Get the point source: HUC dataset
                point_huc_dict = ps_data[['coordinates', 'HUC']].drop_duplicates().set_index('coordinates').to_dict()['HUC']
                points_huc_tuple_rev = [(str(b),a) for a,b in point_huc_dict.items()]
                # Flip it to get the HUC: point sources dataset
                huc_points_dict = {}
                for e in points_huc_tuple_rev:
                    huc_points_dict.setdefault(e[0], set()).add(e[1])
                    
                # huc_points_dict is a dictionary of HUC: point sources
                # Convert this into huc_num_points_dict (NODE DATA)
                huc_data_dict = {key: len(value) for key, value in huc_points_dict.items()}

            else:
                param = huc_parameter.split(' ')[2]
                huc_load = get_load_data(param)
                huc_load_df = huc_load[huc_month:huc_month].transpose().reset_index()
                huc_data_dict = {str(huc):load for huc, load in zip(huc_load_df.iloc[:,0], huc_load_df.iloc[:, 1])}


            
            huc_data[['HUC12', 'TOHUC']] = huc_data[['HUC12', 'TOHUC']].astype(str)
            # Get a dataframe with all the HUC flows, and convert to str
            huc_flows = huc_data[['HUC12', 'TOHUC']]

            # List of unique HUCs (i.e. NODES of DAG), some of them might or might not have point sources
            unique_hucs = pd.unique(huc_flows.values.ravel()).tolist()
            unique_hucs = [e for e in unique_hucs]

            # Instantiate directed graph
            graph = nx.DiGraph()
            # Add nodes, with the property being the # point sources (huc_num_points_dict)
            hucs_to_add = [(huc, {huc_parameter: (huc_data_dict[huc] if (huc in huc_data_dict) else 0)}) for huc in unique_hucs]
            graph.add_nodes_from(hucs_to_add)

            ### Add edges

            # Store the HUC from and to as EDGES of a directed graph
            huc_flows_edges = [(fr, to) for fr, to in zip(huc_flows['HUC12'], huc_flows['TOHUC'])]
            graph.add_edges_from(huc_flows_edges)

            # For all HUCs, get this sum of point sources for all ancestors of a given HUC + itself
            huc_cum_num_points_dict = {huc: sum(graph.nodes[node][huc_parameter] for node in nx.ancestors(graph, huc)) + graph.nodes[huc][huc_parameter]
                                    for huc in unique_hucs}
            huc_cum_num_points_df =  pd.DataFrame(huc_cum_num_points_dict.items())
            huc_cum_num_points_df.columns = ['HUC12', huc_parameter]

            # Merge with original HUC list
            huc_data = huc_data.merge(huc_cum_num_points_df, on = 'HUC12', how = 'left')
            
            colors = set_overlay_colors(huc_data[huc_parameter]) 

                
            huc_points = go.Scattermapbox(
                    lat = huc_data['LAT'],
                    lon = huc_data['LON'],
                    mode = 'markers',
                    marker = go.scattermapbox.Marker(
                            opacity = 0
                    ),
                    text = huc_data[huc_parameter],
                    name = huc_parameter
                )
        
        else:
            
            # Load - need to calculate Load from TN and TP amounts multiplied by the Flow
            if huc_parameter in ['Nitrogen Load', 'Phosphorous Load']:
                param = 'TN' if huc_parameter == 'Nitrogen Load' else 'TP'

                # Reshape to get monthly nutrient load for each HUC
                month_data_huc_pivot = get_load_data(param)                                   

            elif huc_parameter != 'Total Upstream Point Sources':
            
                month_data_huc = ps_data.loc[(ps_data['PARAMETER'] == huc_parameter), ['HUC', 'Month', 'PARAMETER', 'VALUE']] \
                    .groupby(['HUC', 'Month', 'PARAMETER'])['VALUE'].sum().reset_index() \
                    .pivot(index = ['HUC', 'Month'], columns = 'PARAMETER', values = 'VALUE') 
                month_data_huc_pivot = month_data_huc.reset_index() \
                    .pivot(columns = 'HUC', index = 'Month', values = huc_parameter) \
                    .fillna(0)                  

            # Select HUC data for one month
            huc_month = month_data_huc_pivot[huc_month: huc_month].transpose().reset_index()
            huc_month['HUC'] = huc_month['HUC'].astype(str)
            huc_month.columns = ['HUC12', 'Value']

            # Merge the HUC point source data with the HUC data
            huc_data = huc_data.merge(huc_month, on = 'HUC12')                                      
  
            colors = set_overlay_colors(huc_data['Value'])    

            huc_points = go.Scattermapbox(
                    lat = huc_data['LAT'],
                    lon = huc_data['LON'],
                    mode = 'markers',
                    marker = go.scattermapbox.Marker(
                            opacity = 0
                    ),
                    text = huc_data['Value'],
                    name = huc_parameter
                )

        data.append(huc_points)

        # Show HUCs
        layers=[{
            'name': 'Segments',
            'sourcetype': 'geojson',
            'source': json.loads(huc_data['geometry_json'][i]),
            'visible': True,
            'opacity': 0.5,
            'color': colors[i],
            'type': 'fill',   
            } for i in range(len(huc_data))]

    
        mapbox_dict = dict(
                        accesstoken=mapbox_access_token,
                        bearing=0,
                        layers = layers,
                        center= (go.layout.mapbox.Center(
                            lat=39,
                            lon=-76.4
                        )),
                        pitch=0,
                        zoom=7
                    )
    else:
        mapbox_dict = dict(
                        accesstoken=mapbox_access_token,
                        bearing=0,
                        center= (go.layout.mapbox.Center(
                            lat=39,
                            lon=-76.4
                        )),
                        pitch=0,
                        zoom=7
                    )

    
    return {'data': data,
            'layout': go.Layout(
                height = 800,
                width = 1000,
                margin = {'l': 50, 'r': 50, 't': 0, 'b': 0},
                hovermode='closest',
                showlegend = True,
                mapbox = mapbox_dict 
            )
    }



if __name__ == '__main__':
    app.run_server(debug=False)