import pandas as pd
import dash
import os
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# ==========================================
# CONFIGURATION & DATA LOADING
# ==========================================

# Ensure the script finds the data regardless of execution directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "spacex_launch_dash.csv")

def load_launch_data(path):
    # Initialise the data engine
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found at {path}")
    return pd.read_csv(path)

spacex_df = load_launch_data(DATA_PATH)
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# ==========================================
# LOGIC FUNCTIONS (Data Processing)
# ==========================================

def get_site_options(df):
    # Generate labels for the dropdown dynamically
    options = [{'label': 'All Sites', 'value': 'ALL'}]
    for site in sorted(df['Launch Site'].unique()):
        options.append({'label': site, 'value': site})
    return options

def build_pie_chart(df, site):
    # Logic to calculate success vs failure ratios
    if site == 'ALL':
        fig = px.pie(df, values='class', 
                     names='Launch Site', 
                     title='Total Success Launches By Site')
    else:
        filtered_df = df[df['Launch Site'] == site]
        success_counts = filtered_df['class'].value_counts().reset_index()
        success_counts.columns = ['outcome', 'count']
        success_counts['outcome'] = success_counts['outcome'].map({1: 'Success', 0: 'Failure'})
        
        fig = px.pie(success_counts, values='count', 
                     names='outcome', 
                     title=f"Total Success Launches for {site}",
                     color='outcome',
                     color_discrete_map={'Success':'#2ca02c', 'Failure':'#d62728'})
    return fig

def build_scatter_chart(df, site, payload_range):
    # Filter by payload range first
    low, high = payload_range
    mask = (df['Payload Mass (kg)'] >= low) & (df['Payload Mass (kg)'] <= high)
    filtered_df = df[mask]
    
    # Further filter by site if necessary
    if site != 'ALL':
        filtered_df = filtered_df[filtered_df['Launch Site'] == site]
        title = f"Correlation between Payload and Success for {site}"
    else:
        title = "Correlation between Payload and Success for all Sites"
    
    fig = px.scatter(
        filtered_df, x="Payload Mass (kg)", y="class", 
        color="Booster Version Category",
        title=title
    )
    return fig

# ==========================================
# APP LAYOUT
# ==========================================

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),
    
    # TASK 1: Site Selection Dropdown
    html.Div([
        html.Label("Select Launch Site:"),
        dcc.Dropdown(
            id='site-dropdown',
            options=get_site_options(spacex_df),
            value='ALL',
            placeholder="Select a Launch Site here",
            searchable=True
        ),
    ]),
    html.Br(),

    # TASK 2: Success Pie Chart Output
    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    # TASK 3: Payload Range Slider
    html.P("Payload range (Kg):"),
    dcc.RangeSlider(
        id='payload-slider',
        min=0, max=10000, step=1000,
        marks={i: f'{i}' for i in range(0, 10001, 2500)},
        value=[min_payload, max_payload]
    ),

    # TASK 4: Success-Payload Scatter Chart Output
    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
])

# ==========================================
# CALLBACKS (Reactive Updates)
# ==========================================

@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def update_pie(entered_site):
    return build_pie_chart(spacex_df, entered_site)

@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    [Input(component_id='site-dropdown', component_property='value'), 
     Input(component_id='payload-slider', component_property='value')]
)
def update_scatter(entered_site, payload_range):
    return build_scatter_chart(spacex_df, entered_site, payload_range)

# ==========================================
# SERVER INITIALISATION
# ==========================================

if __name__ == '__main__':
    app.run(debug=True)