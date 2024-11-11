# Import necessary libraries
import plotly.graph_objs as go
import pandas as pd
import panel as pn
import sqlite3
import numpy as np

# Initialize Panel extension
pn.extension('plotly')
pn.extension('tabulator')

# Connect to the database and load data
conn = sqlite3.connect('MESI.db')
df_main = pd.read_sql_query("SELECT * FROM Site_main", conn)
df_metadata = pd.read_sql_query("SELECT * FROM Site_metadata", conn)
conn.close()

# Extract unique values
unique_sites = df_main['site'].dropna().unique().tolist()
unique_lats = df_main['lat'].dropna()
unique_lons = df_main['lon'].dropna()

# Create MultiChoice widget for selecting sites
site_select = pn.widgets.MultiChoice(
    name='Select Site', options=df_main['site'].dropna().unique().tolist(), value=[],
    placeholder='Select one or more sites',
    width=180
)

# Latitude and Longitude range sliders
lat_slider = pn.widgets.RangeSlider(
    name='Latitude slider', bar_color='skyblue',
    start=unique_lats.min(), end=unique_lats.max(), step=0.5,
    value=(unique_lats.min(), unique_lats.max())
)

lon_slider = pn.widgets.RangeSlider(
    name='Longitude slider', bar_color='skyblue',
    start=unique_lons.min(), end=unique_lons.max(), step=0.5,
    value=(unique_lons.min(), unique_lons.max())
)

# Initialize DataFrame widget for displaying data
site_data_table = pn.widgets.Tabulator(pd.DataFrame(), height=500, width=310, show_index=False)

# Define selected data option and initial site filter
selected_option = "all"  # Default option for showing all data

# Define function to filter data based on button selection and site_select
def update_table(event=None):
    global selected_option
    # Get the currently selected sites
    selected_sites = site_select.value

    # Check selected_option to decide which data to show
    if selected_option == "Site_cite":
        filtered_df = df_main[['site', 'lat', 'lon', 'citation', 'study']]
    elif selected_option == "Site_meta":
        filtered_df = df_metadata
    elif selected_option == "Site_data":
        filtered_df = df_main[['site', 'lat', 'lon', 'treatment', 'response', 'x_c', 'x_t', 'x_units']]
    else:  # Default: show all data in Site_main if "all" is selected
        filtered_df = df_main

    # Apply site filtering if there are selected sites
    if selected_sites:
        filtered_df = filtered_df[filtered_df['site'].isin(selected_sites)]

    # Update the table display
    site_data_table.value = filtered_df if not filtered_df.empty else pd.DataFrame(columns=filtered_df.columns)

# Define button click handlers to update the selected_option and refresh table
def select_site_cite(event):
    global selected_option
    selected_option = "Site_cite"
    button_site_cite.button_type = 'danger'  # Change color to red when selected
    button_site_meta.button_type = 'primary'
    button_site_data.button_type = 'primary'
    update_table()

def select_site_meta(event):
    global selected_option
    selected_option = "Site_meta"
    button_site_cite.button_type = 'primary'
    button_site_meta.button_type = 'danger'  # Change color to red when selected
    button_site_data.button_type = 'primary'
    update_table()

def select_site_data(event):
    global selected_option
    selected_option = "Site_data"
    button_site_cite.button_type = 'primary'
    button_site_meta.button_type = 'primary'
    button_site_data.button_type = 'danger'  # Change color to red when selected
    update_table()

# Reset to show all data
def show_all_data(event):
    global selected_option
    selected_option = "all"
    button_site_cite.button_type = 'primary'
    button_site_meta.button_type = 'primary'
    button_site_data.button_type = 'primary'
    update_table()

# Define buttons and set their callbacks
button_site_cite = pn.widgets.Button(name='Site_cite', button_type='primary')
button_site_meta = pn.widgets.Button(name='Site_meta', button_type='primary')
button_site_data = pn.widgets.Button(name='Site_data', button_type='primary')
button_show_all = pn.widgets.Button(name='Show All', button_type='success')  # New button to reset to show all data

button_site_cite.on_click(select_site_cite)
button_site_meta.on_click(select_site_meta)
button_site_data.on_click(select_site_data)
button_show_all.on_click(show_all_data)  # Add callback for the "Show All" button

# Watch for site selection changes and update table accordingly
site_select.param.watch(update_table, 'value')

# Define map plotting function
@pn.depends(site_select.param.value, lat_slider.param.value, lon_slider.param.value)
def plot_map(selected_sites, lat_range, lon_range):
    # Filter data by latitude and longitude range
    filtered_df = df_main[(df_main['lat'].between(*lat_range)) & (df_main['lon'].between(*lon_range))]
    filtered_df['color'] = filtered_df['site'].apply(lambda x: 'red' if x in selected_sites else 'blue')

    # Create Plotly map
    fig = go.Figure(go.Scattergeo(
        lon=filtered_df['lon'],
        lat=filtered_df['lat'],
        text=filtered_df['site'],
        mode='markers',
        marker=dict(size=3, color=filtered_df['color'], symbol='circle'),
        hoverinfo='text'
    ))

    fig.update_layout(
        title='',
        geo=dict(projection_type='natural earth', showland=True, landcolor="lightgray", coastlinecolor="white"),
        margin=dict(l=0, r=0, t=0, b=0),
        width=700, height=600  # Adjusted width and height for map size
    )
    return fig

# Create a Plotly panel for the map and set up click event handling
plot_pane = pn.pane.Plotly(plot_map)

# Click event handler function
def handle_click(event):
    if 'points' in event.new and len(event.new['points']) > 0:
        clicked_site = event.new['points'][0]['text']
        if clicked_site in site_select.value:
            site_select.value = [site for site in site_select.value if site != clicked_site]
        else:
            site_select.value = site_select.value + [clicked_site]
    else:
        print("Click event did not return expected data format:", event)

# Watch for click events on plot_pane and trigger handle_click
plot_pane.param.watch(handle_click, 'click_data')

# Header with three buttons
header = pn.Row(
    pn.layout.HSpacer(),
    pn.pane.Markdown("# MESI DASH", styles={'text-align': 'center', 'font-size': '20px'}),
    pn.layout.HSpacer(),
    height=100  # Fixed height for header
)

# Main dashboard layout with fixed width percentages
control_panel = pn.Column(
pn.Spacer(height=100),
    site_select, lat_slider, lon_slider, pn.Row(button_site_cite, button_site_meta), pn.Row(button_site_data, button_show_all),  width=200,
)

# Create dropdown widgets for treatment and response
treatment_select = pn.widgets.Select(name='Select Treatment', options=['f'], width = 180)  # Extend options as needed
response_select = pn.widgets.Select(name='Select Response', options=['agb'], width = 180)  # Extend options as needed
treatres_panel = pn.Column(
pn.Spacer(height=100),
    treatment_select, response_select, width=200,
)

# Function to filter and calculate ratio based on treatment and response
def calculate_ratio(treatment, response):
    df_filtered = df_main[(df_main['treatment'] == treatment) & (df_main['response'] == response)].copy()

    # Convert 'x_t' and 'x_c' to float and remove invalid values
    df_filtered['x_t'] = pd.to_numeric(df_filtered['x_t'], errors='coerce')
    df_filtered['x_c'] = pd.to_numeric(df_filtered['x_c'], errors='coerce')
    df_filtered = df_filtered.dropna(subset=['x_t', 'x_c'])
    df_filtered = df_filtered[(df_filtered['x_t'] > 0) & (df_filtered['x_c'] > 0)]

    # Calculate log ratio
    df_filtered['ratio'] = np.log(df_filtered['x_t'] / df_filtered['x_c'])

    # Group by site, lat, lon, ecosystem_type and calculate mean ratio
    df_grouped_mean = df_filtered.groupby(['site', 'lat', 'lon', 'ecosystem_type']).ratio.mean().reset_index()

    return df_grouped_mean

# Define a function to create and update the ratio map
@pn.depends(treatment_select.param.value, response_select.param.value)
def update_ratio_map(treatment, response):
    df_grouped = calculate_ratio(treatment, response)

    # Calculate quantiles for color scale
    lower_bound = df_grouped['ratio'].quantile(0.10)
    upper_bound = df_grouped['ratio'].quantile(0.90)

    # Create Plotly scatter map
    fig = go.Figure(go.Scattergeo(
        lon=df_grouped['lon'],
        lat=df_grouped['lat'],
        text=df_grouped['site'] + ' ' + df_grouped['ecosystem_type'] + ' ' + df_grouped['ratio'].astype(str),
        mode='markers',
        marker=dict(
            size=3,
            color=df_grouped['ratio'],
            colorscale='Bluered',
            cmin=lower_bound,
            cmax=upper_bound,
            colorbar=dict(title="Ratio")
        )
    ))

    # Update map layout
    fig.update_layout(
        title='World Map with Ratio-colored Points',
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor="lightgray",
            coastlinecolor="white"
        ),
    )

    return fig
ratio_plot_pane = pn.pane.Plotly(update_ratio_map)

main_dashboard = pn.Row(
    control_panel,
    pn.Spacer(width=30),
    pn.Column(plot_pane, width=700),  # Increased map width
    pn.Spacer(width=30),
    pn.Column(site_data_table, width=200)  # Adjusted table width for balance
)

ratio_dashboard = pn.Row(treatres_panel, pn.Spacer(width=30), pn.Column(ratio_plot_pane, width=700))

# Analytics and Model placeholder pages
analytics_dashboard = pn.Column(
    pn.pane.Markdown("# Analytics Page (Coming Soon)", styles={'font-size': '20px', 'text-align': 'center'}),
)
model_dashboard = pn.Column(
    pn.pane.Markdown("# Model Page (Coming Soon)", styles={'font-size': '20px', 'text-align': 'center'}),
)

# Tabs interface with three pages
tabs = pn.Tabs(
    ("Main", pn.Column(header, main_dashboard, pn.Spacer(height =30), ratio_dashboard)),
    ("Analytics", pn.Column(header, analytics_dashboard)),
    ("Model", pn.Column(header, model_dashboard)),
)

# Bind the update_table function to ensure table refresh
table_panel = pn.panel(update_table)

# Display the app
app = pn.Column(tabs, table_panel)
pn.serve(app, port=8000, address="0.0.0.0", allow_websocket_origin=["mesi-dash-demo.onrender.com"])
