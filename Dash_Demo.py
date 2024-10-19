import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3
import plotly.graph_objs as go

# 创建 Dash 应用
app = dash.Dash(__name__)


# 连接到 SQLite 数据库并读取 Site_main 表格数据
def get_site_main():
    conn = sqlite3.connect('MESI.db')
    df = pd.read_sql_query("SELECT * FROM Site_main", conn)
    conn.close()
    return df


df_site_main = get_site_main()

# 获取唯一的 site、lat 和 lon 信息
unique_sites = df_site_main['site'].dropna().unique()
unique_lats = df_site_main['lat'].dropna().unique()
unique_lons = df_site_main['lon'].dropna().unique()

# 创建 Dash 应用的布局
app.layout = html.Div([
    html.H1('Site World Map'),

    # 地图展示
    dcc.Graph(id='world-map', config={'scrollZoom': False}),

    # 下拉菜单选择 site
    html.Label("Select Site:"),
    dcc.Dropdown(
        id='site-dropdown',
        options=[{'label': site, 'value': site} for site in unique_sites],
        placeholder="Select a site",
        multi=True  # 允许多选
    ),

    # 下拉菜单选择 lat
    html.Label("Select Latitude (Optional):"),
    dcc.Dropdown(
        id='lat-dropdown',
        options=[{'label': str(lat), 'value': lat} for lat in unique_lats],
        placeholder="Select a latitude",
        multi=True  # 允许多选
    ),

    # 下拉菜单选择 lon
    html.Label("Select Longitude (Optional):"),
    dcc.Dropdown(
        id='lon-dropdown',
        options=[{'label': str(lon), 'value': lon} for lon in unique_lons],
        placeholder="Select a longitude",
        multi=True  # 允许多选
    ),

    # 点击 site 后展示相关信息
    html.Hr(),
    html.Div(id='site-data')
])


# 更新地图，根据 site, lat, lon 筛选
@app.callback(
    Output('world-map', 'figure'),
    [Input('site-dropdown', 'value'),
     Input('lat-dropdown', 'value'),
     Input('lon-dropdown', 'value')]
)
def update_map(selected_sites, selected_lats, selected_lons):
    filtered_df = df_site_main

    # 根据选择的 site, lat, lon 进行筛选
    if selected_sites:
        filtered_df = filtered_df[filtered_df['site'].isin(selected_sites)]
    if selected_lats:
        filtered_df = filtered_df[filtered_df['lat'].isin(selected_lats)]
    if selected_lons:
        filtered_df = filtered_df[filtered_df['lon'].isin(selected_lons)]

    # 创建地图
    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lon=filtered_df['lon'],  # 经度
        lat=filtered_df['lat'],  # 纬度
        text=filtered_df['site'],  # 悬停显示 site 名字
        mode='markers',  # 以点的方式展示
        marker=dict(
            size=2,  # 将点的大小设置为 4
            color='blue',  # 设置点的颜色
            symbol='circle'
        )
    ))

    # 设置地图的布局
    fig.update_layout(
        title='Geographical Distribution of Sites',
        geo=dict(
            projection_type='natural earth',  # 自然地球投影
            showland=True,  # 显示陆地
            landcolor="lightgray",
            coastlinecolor="white",
        )
    )

    return fig


# 定义回调函数，处理点击事件并展示 site 数据
@app.callback(
    Output('site-data', 'children'),
    [Input('world-map', 'clickData')]
)
def display_site_data(clickData):
    if clickData is None:
        return html.Div("Click on a site to see details.")

    # 从点击的数据中提取 site 名称
    clicked_site = clickData['points'][0]['text']

    # 根据 site 名称从数据框中获取相关数据
    site_info = df_site_main[df_site_main['site'] == clicked_site]

    if site_info.empty:
        return html.Div("No data available for the selected site.")

    # 将 site 的信息转换为 HTML 表格或文本展示
    return html.Table([
        html.Tr([html.Th(col) for col in site_info.columns]),  # 表头
        html.Tr([html.Td(site_info.iloc[0][col]) for col in site_info.columns])  # 表体
    ])


# 运行应用
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
