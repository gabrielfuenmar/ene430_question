
'''
Author:Gabriel Fuentes
gabriel.fuentes@snf.no'''

import pathlib
import dash
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px

##DataFrames
import pandas as pd
import geopandas as gpd
import os
import requests

    
##Databases
###Pressure

pres=gpd.read_file("data/contour.geojson") 
pres["geometry"]=pres.geometry.buffer(0.1)

##routes
routes=pd.read_parquet("data/routes")


values=[[0,"Panama Canal","Cristobal","Kashima","GC",8531,6.12,425,638],
        [3,"Panama Canal","Cristobal","Kashima","RL",9825,7.0,425,580],
        [9,"Cape Horn","Kashima","Kashima","RL",17008,11.6,375,1525],
        [6,"Cape Horn","Kashima","Kashima","GC",16482,11.3,375,1708],
        [1,"Panama Canal","Busan","Qingdao","GC",10082,5.83,390,720],
        [2,"Panama Canal","Cristobal","Qingdao","GC",10081,5.85,425,717],
        [4,"Panama Canal","Busan","Qingdao","RL",11121,6.43,390,648],
        [5,"Panama Canal","Cristobal","Qingdao","RL",11120,6.45,390,645],
        [8,"Cape Horn","Busan","Qingdao","GC",17079,9.49,390,1875],
        [7,"Cape Horn","Busan","Qingdao","RL",18088,10.05,390,1800]]

values=pd.DataFrame(values,columns=["route","passage","bunker","discharge",
                                    "navigation","miles","speed","bunker_price","bunker_consumption"])

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

app.title = 'Voyage Calculator ENE 430'

server = app.server

# Create global chart template

MAPBOX_TOKEN =os.environ.get('MAPBOX_TOKEN', None)

layout_map = dict(
    height=400,
    paper_bgcolor='#30333D',
    plot_bgcolor='#30333D',
    margin=dict(l=10, r=10, b=10, t=40),
    hovermode="closest",
    font=dict(family="HelveticaNeue",size=17,color="#B2B2B2"),
    legend=dict(font=dict(size=10), orientation="h"),
    title="<b>Route Summary</b>",
    mapbox=dict(
        accesstoken=MAPBOX_TOKEN,
        style='mapbox://styles/gabrielfuenmar/ckkmdsqrm4ngq17o21tnno1ce',
        center=dict(lon=-85.00, lat=8.93),
        zoom=2,
    ),
    showlegend=False,
)
layout= dict( 
    legend=dict(bgcolor='rgba(0,0,0,0)',font=dict(size=14,family="HelveticaNeue")),
    font_family="HelveticaNeue",
    font_color="#B2B2B2",
    title_font_family="HelveticaNeue",
    title_font_color="#B2B2B2",
    title_font_size=20,
    paper_bgcolor='#21252C',
    plot_bgcolor='#21252C',
    xaxis=dict(gridcolor="rgba(178, 178, 178, 0.1)",title_font_size=15,
               tickfont_size=14,title_font_family="HelveticaNeue",tickfont_family="HelveticaNeue"),
    yaxis=dict(gridcolor="rgba(178, 178, 178, 0.1)",title_font_size=15,tickfont_size=14,
               title_font_family="HelveticaNeue",tickfont_family="HelveticaNeue")
    )

##Modebar on graphs
config={"displaylogo":False, 'modeBarButtonsToRemove': ['autoScale2d']}
###Map

map_fig=px.choropleth_mapbox(pres,
                            geojson=pres.geometry,
                            locations=pres.index,
                            color=pres["level-value"],
                            color_discrete_map=pd.Series(pres.stroke.values,index=pres["level-index"]).to_dict(),
                            opacity=0.3,
                            hover_name=pres.title)

map_fig.update_layout(layout_map)

##Annotation on graphs
annotation_layout=dict(
    xref="x domain",
    yref="y domain",
    x=0.25,
    y=-0.35)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2(
                                    "Voyage Calculator",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Question for the day. Lecture 4 ENE 430", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(html.Button("Refresh", id="refresh-button")
                               ,href="https://ene430.herokuapp.com"), 
                        html.A(
                            html.Button("Developer", id="home-button"),
                            href="https://gabrielfuentes.org",
                        )                  
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div([html.P("Navigation type:", className="control_label"),
                                  dcc.RadioItems(
                            id='selector_gc',options=[{'label': "Great Circle Navigation", 'value': "GC"},
                                                      {'label': "Rhumb Line Navigation", 'value': "RL"}],
                            value="RL",labelStyle={'display': 'inline-block'})]),
                        html.Div([html.P("Panama Canal or Cape Horn:", className="control_label"),
                        dcc.RadioItems(
                            id='selector_pc',options=[{'label': "Panama Canal", 'value': "Panama Canal"},
                                                      {'label': "Cape Horn", 'value': "Cape Horn"}],
                            value="Panama Canal",labelStyle={'display': 'inline-block'})]),
                        
                        html.P("Destination Port:", className="control_label"),
                        dcc.Dropdown(
                            id='destination-dropdown',
                            options=[{'label': row,'value': row} \
                                     for row in sorted(values.discharge.unique())],
                                    placeholder="All",
                                    className="dcc_control"),
                        html.P("Bunker Port:", className="control_label"),
                        dcc.Dropdown(
                            id='bunker-dropdown',
                            options=[{'label': row,'value': row} \
                                     for row in sorted(values.bunker.unique())],
                                    placeholder="All",
                                    className="dcc_control"),
                    
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.P("Speed (kts)"),html.H6(id="speedText")],
                                    id="speed",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.P("Miles (NM)"),html.H6(id="milesText")],
                                    id="miles",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.P("Consumption (MT)"),html.H6(id="consText")],
                                    id="cons",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.P("Bunker Price"),html.H6(id="priceText")],
                                    id="price",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div([
                            html.Div(
                                [dcc.Graph(animate=True,config=config,id="map_in"),
                                                         dcc.Checklist(
                                                             id='selector',options=[{'label': "Atm. Pressure", 'value': "Atm"}],
                                                             value=[])
                                 ],
                                id="MapContainer",
                                className="pretty_container twelve columns",
                                )
                            ],
                            className="row flex-display",
                            ),
                        ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

   
def trip_map(bunker=None,destination=None,nav=None,pc=None,trigger=False):
    route_in=routes.copy()
    values_in=values.copy()
    
    values_in=values_in[((values_in.bunker==bunker)&(values_in.discharge==destination)&\
                        (values_in.navigation==nav)&(values_in.passage==pc))]
                               
    ###Map
    if values_in.shape[0]!=0 and trigger is True:
        map_fig=px.choropleth_mapbox(pres,
                        geojson=pres.geometry,
                        locations=pres.index,
                        color=pres["level-value"],
                        color_continuous_scale=px.colors.sequential.Inferno_r,
                        range_color=(900, 1100),
                        opacity=0.3,
                        hover_name=pres.title)
        map_fig.update_layout(layout_map)
        map_fig.layout.coloraxis.colorbar.title = 'Pa'
        
        route_in=route_in[route_in.number==values_in.iloc[0].route]
        
        lons=[]
        lats=[]
        for index, row in route_in.groupby("number"):
            lons.append(row.lon.values.tolist()) 
            lats.append(row.lat.values.tolist())
        
        for i in range(len(lons)):
            map_fig.add_trace(go.Scattermapbox(mode="markers+lines",
                                      lon=lons[i],
                                      lat=lats[i]))

        return map_fig
    
    elif values_in.shape[0]==0 and trigger is True:
        map_fig_2=px.choropleth_mapbox(pres,
                        geojson=pres.geometry,
                        locations=pres.index,
                        color=pres["level-value"],
                        color_continuous_scale=px.colors.sequential.Inferno_r,
                        range_color=(900, 1100),
                        opacity=0.3,
                        hover_name=pres.title)
        map_fig_2.update_layout(layout_map)
        map_fig_2.layout.coloraxis.colorbar.title = 'Pa'
        
        return map_fig_2
    elif values_in.shape[0]!=0 and trigger is False:
        map_fig_3=go.Figure(go.Scattermapbox(lat=["45.1"],lon=["-80.0"], mode='markers'))
        route_in=route_in[route_in.number==values_in.iloc[0].route]
        
        lons=[]
        lats=[]
        for index, row in route_in.groupby("number"):
            lons.append(row.lon.values.tolist()) 
            lats.append(row.lat.values.tolist())
        
        for i in range(len(lons)):
            map_fig_3.add_trace(go.Scattermapbox(mode="markers+lines",
                                      lon=lons[i],
                                      lat=lats[i]))
            map_fig_3.update_layout(layout_map)
            map_fig_3.layout.coloraxis.colorbar.title = 'Pa'

        return map_fig_3

            
    else:
        fig_res=go.Figure(go.Scattermapbox(lat=["45.1"],lon=["-80.0"], mode='markers'))
        fig_res.update_layout(layout_map)
        
        return fig_res
    
    
@app.callback(
    [
    Output("speedText", "children"),
    Output("milesText", "children"),
    Output("consText", "children"),
    Output("priceText","children"),
    ],
    [Input('selector_gc', "value"),
     Input('selector_pc',"value"),
     Input('destination-dropdown', 'value'),
     Input('bunker-dropdown', 'value'),
     ],
)

def updaterow(gc,pc,dest,bunker):
    values_u=values.copy()
    
    values_u=values_u[((values_u.bunker==bunker)&(values_u.discharge==dest)&\
                        (values_u.navigation==gc)&(values_u.passage==pc))]
    if values_u.shape[0]!=0:
        return "{:.1f}".format(values_u.iloc[0].speed),format(values_u.iloc[0].miles,","),format(values_u.iloc[0].bunker_consumption,","), "${}/MT".format(values_u.iloc[0].bunker_price)
        
    else:
        return "NA","NA","NA","NA"
    
@app.callback(
    Output("map_in", "figure"),
    [
     Input('selector_gc', "value"),
     Input('selector_pc',"value"),
     Input('destination-dropdown', 'value'),
     Input('bunker-dropdown', 'value'),
     Input("selector","value")
     ],
)

def update_map(gc,pc,dest,bunker,trigger_val):
    
    if not trigger_val:
        emission_fig=trip_map(bunker=bunker,destination=dest,nav=gc,pc=pc,trigger=False)
        
    else:
        emission_fig=trip_map(bunker=bunker,destination=dest,nav=gc,pc=pc,trigger=True)
    

    return emission_fig

# Main
if __name__ == "__main__":
    app.run_server(debug=True)
