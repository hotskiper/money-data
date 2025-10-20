import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# 读取 Excel 数据
df = pd.read_excel("盖世研究院_汽车品牌销量_透视.xlsx")

# 如果第一列是品牌索引，要 reset_index
if "品牌" not in df.columns:
    df = df.reset_index()

# 转换年月列为 datetime 类型
df.columns = [str(c) for c in df.columns]
date_cols = [c for c in df.columns if c != "品牌"]
df_melt = df.melt(id_vars="品牌", value_vars=date_cols, var_name="年月", value_name="销量")

# 处理年月格式
df_melt["年月"] = pd.to_datetime(df_melt["年月"], format="%Y-%m", errors="coerce")
df_melt = df_melt.dropna(subset=["年月"])

# 增加“年份”列
df_melt["年份"] = df_melt["年月"].dt.year

# 创建 Dash 应用
app = Dash(__name__)
app.title = "盖世研究院汽车品牌销量分析"

# 布局
app.layout = html.Div([
    html.H2("📈 盖世研究院汽车品牌销量趋势", style={"textAlign": "center"}),

    html.Div([
        html.Label("选择品牌："),
        dcc.Dropdown(
            options=[{"label": b, "value": b} for b in sorted(df_melt["品牌"].unique())],
            value=["大众", "丰田", "奔驰", "宝马", "奥迪", "理想", "问界"],
            multi=True,
            id="brand-dropdown"
        ),
    ], style={"width": "40%", "display": "inline-block", "padding": "10px"}),

    html.Div([
        html.Label("时间维度："),
        dcc.RadioItems(
            options=[
                {"label": "按月显示", "value": "month"},
                {"label": "按年显示", "value": "year"},
            ],
            value="month",
            id="time-mode",
            inline=True
        ),
    ], style={"width": "40%", "display": "inline-block", "padding": "10px"}),

    html.Div([
        html.Label("筛选年份："),
        html.Div([
            dcc.Dropdown(
                id="year-start",
                options=[{"label": str(y), "value": int(y)} for y in sorted(df_melt["年份"].unique())],
                value=int(df_melt["年份"].min()),
                clearable=False,
                style={"width": "48%", "display": "inline-block", "marginRight": "4%"}
            ),
            dcc.Dropdown(
                id="year-end",
                options=[{"label": str(y), "value": int(y)} for y in sorted(df_melt["年份"].unique())],
                value=int(df_melt["年份"].max()),
                clearable=False,
                style={"width": "48%", "display": "inline-block"}
            ),
        ])
    ], style={"width": "40%", "display": "inline-block", "padding": "10px"}),

    dcc.Graph(id="sales-graph", style={"height": "600px"})
])

# 回调函数
@app.callback(
    Output("sales-graph", "figure"),
    Input("brand-dropdown", "value"),
    Input("time-mode", "value"),
    Input("year-start", "value"),
    Input("year-end", "value")
)
def update_chart(selected_brands, time_mode, year_start, year_end):
    if not selected_brands:
        return px.line(title="请选择至少一个品牌")

    # 处理年份范围
    if year_start is None:
        year_start = int(df_melt["年份"].min())
    if year_end is None:
        year_end = int(df_melt["年份"].max())
    if year_start > year_end:
        year_start, year_end = year_end, year_start

    df_filtered = df_melt[(df_melt["品牌"].isin(selected_brands)) & (df_melt["年份"].between(year_start, year_end))]

    if time_mode == "year":
        df_grouped = (
            df_filtered.groupby(["年份", "品牌"], as_index=False)["销量"].sum()
        )
        fig = px.line(
            df_grouped, x="年份", y="销量", color="品牌",
            markers=True, title="各品牌年度销量趋势"
        )
    else:
        fig = px.line(
            df_filtered, x="年月", y="销量", color="品牌",
            markers=False, title="各品牌月度销量趋势"
        )

    fig.update_layout(
        xaxis_title="时间",
        yaxis_title="销量（辆）",
        hovermode="x unified",
        template="plotly_white"
    )

    # 设置横坐标范围
    if time_mode == "year":
        fig.update_xaxes(range=[year_start, year_end])
    else:
        start_dt = pd.Timestamp(f"{year_start}-01-01")
        end_dt = pd.Timestamp(f"{year_end}-12-31")
        fig.update_xaxes(range=[start_dt, end_dt])

    return fig


if __name__ == "__main__":
    app.run(debug=True, port=8050)
