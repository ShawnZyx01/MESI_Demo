
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import panel as pn
import sqlite3
# Initialize Panel extension
pn.extension('plotly')
pn.extension('tabulator')
# Assume df_main contains all site, lat, lon, and experiment data
conn = sqlite3.connect('MESI.db')
df_main = pd.read_sql_query("SELECT * FROM Site_main", conn)
conn.close()

# Extract unique values
unique_sites = df_main['site'].dropna().unique().tolist()
unique_lats = df_main['lat'].dropna()
unique_lons = df_main['lon'].dropna()

# Create MultiChoice widget for selecting sites
site_select = pn.widgets.MultiChoice(
    name='Select Site', options=unique_sites, value=[],
    placeholder='Select one or more sites', sizing_mode='stretch_width'
)

# Latitude range slider
lat_slider = pn.widgets.RangeSlider(
    name='Latitude slider', bar_color='skyblue',
    start=unique_lats.min(), end=unique_lats.max(), step=0.5,
    value=(unique_lats.min(), unique_lats.max())
)

# Longitude range slider
lon_slider = pn.widgets.RangeSlider(
    name='Longitude slider', bar_color='skyblue',
    start=unique_lons.min(), end=unique_lons.max(), step=0.5,
    value=(unique_lons.min(), unique_lons.max())
)

# Data display table
site_data_table = pn.widgets.DataFrame(sizing_mode='stretch_width', height=500, width=50)


# Define map plotting function
@pn.depends(site_select.param.value, lat_slider.param.value, lon_slider.param.value)
def plot_map(selected_sites, lat_range, lon_range):
    # Filter data by latitude and longitude range
    filtered_df = df_main[(df_main['lat'].between(*lat_range)) & (df_main['lon'].between(*lon_range))]

    # Set point color based on selection
    filtered_df['color'] = filtered_df['site'].apply(lambda x: 'red' if x in selected_sites else 'blue')

    # Create Plotly map
    fig = go.Figure(go.Scattergeo(
        lon=filtered_df['lon'],
        lat=filtered_df['lat'],
        text=filtered_df['site'],
        mode='markers',
        marker=dict(
            size=3,
            color=filtered_df['color'],
            symbol='circle'
        ),
        hoverinfo='text'
    ))

    # Map layout settings
    fig.update_layout(
        title='Geographical Distribution of Sites',
        geo=dict(projection_type='natural earth', showland=True, landcolor="lightgray", coastlinecolor="white"),
        width=800, height=800
    )
    return fig


# Create a Plotly panel for the map and set up click event handling
plot_pane = pn.pane.Plotly(plot_map, sizing_mode='stretch_both')


# Click event handler function
def handle_click(event):
    if 'points' in event.new and len(event.new['points']) > 0:
        clicked_site = event.new['points'][0]['text']

        # Toggle selection in site_select widget
        if clicked_site in site_select.value:
            site_select.value = [site for site in site_select.value if site != clicked_site]
        else:
            site_select.value = site_select.value + [clicked_site]

        # Update data table
        selected_data = df_main[df_main['site'].isin(site_select.value)]
        site_data_table.value = selected_data
    else:
        print("Click event did not return expected data format:", event)


# Watch for click events on plot_pane and trigger handle_click
plot_pane.param.watch(handle_click, 'click_data')

# Header with three buttons
header = pn.Row(
    pn.pane.Markdown("# MESI DASH", style={'text-align': 'center', 'font-size': '10px', 'flex-grow': '1'}),
    sizing_mode='stretch_width'
)

# Main dashboard layout
control_panel = pn.Column(
    site_select,
    lat_slider,
    lon_slider,
    width=200
)
main_dashboard = pn.Row(
    control_panel,
    pn.Spacer(width=30),
    pn.Column(plot_pane, sizing_mode='stretch_both', min_width=800),
    pn.Spacer(width=30),
    pn.Column(site_data_table, min_width=50)
)

# Analytics and Model placeholder pages
analytics_dashboard = pn.Column(
    pn.pane.Markdown("# Analytics Page (Coming Soon)", style={'font-size': '6px', 'text-align': 'center'}),
    sizing_mode='stretch_both'
)
model_dashboard = pn.Column(
    pn.pane.Markdown("# Model Page (Coming Soon)", style={'font-size': '6px', 'text-align': 'center'}),
    sizing_mode='stretch_both'
)

# Tabs interface with three pages
tabs = pn.Tabs(
    ("Main", pn.Column(header, main_dashboard)),
    ("Analytics", pn.Column(header, analytics_dashboard)),
    ("Model", pn.Column(header, model_dashboard)),
    sizing_mode='stretch_both'
)

# Show dashboard
tabs.show()
