import akshare as ak
import pandas as pd
from datetime import datetime
import os

# ------------------------------
# 1. 设置起止年月
# ------------------------------
start_year = 2025
start_month = 10
end_year = 2025
end_month = 10

date_list = []
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        if year == end_year and month > end_month:
            break
        date_list.append(f"{year}-{month}")  # 格式 "2002-1"

all_data = []

# ------------------------------
# 2. 遍历抓取每月品牌榜
# ------------------------------
for date_str in date_list:
    date_api = date_str.replace("-", "")  # 接口参数 "200201"
    try:
        df = ak.car_sale_rank_gasgoo(symbol="品牌榜", date=date_api)
        if df.empty:
            continue
        # 当月销量列一般是第2列
        sales_col = df.columns[1]
        df_month = df[["品牌", sales_col]].copy()
        # 重命名为统一列名 '销量'
        df_month.rename(columns={sales_col: "销量"}, inplace=True)
        df_month["年月"] = date_str
        all_data.append(df_month)
        print(f"{date_str} 数据抓取成功")
    except Exception as e:
        print(f"{date_str} 数据抓取失败: {e}")

# ------------------------------
# 3. 合并所有月份数据
# ------------------------------
if all_data:
    result = pd.concat(all_data, ignore_index=True)
    result["年月"] = pd.to_datetime(result["年月"], format="%Y-%m")

# 重新按时间排序
    result = result.sort_values("年月")
else:
    print("没有抓到数据！")
    exit()

# ------------------------------
# 4. 透视表整理成品牌为行，时间为列
# ------------------------------
pivot_df = result.pivot(index="品牌", columns="年月", values="销量")
pivot_df.columns = pivot_df.columns.strftime("%Y-%m")

# ------------------------------
# 5. 保存到 Excel（若已存在则补齐缺失时间段）
# ------------------------------
output_path = "盖世研究院_汽车品牌销量_透视2.xlsx"

# 确保行索引为品牌，列为字符串年月
pivot_df.index.name = "品牌"
pivot_df.columns = [str(c) for c in pivot_df.columns]

if os.path.exists(output_path):
    try:
        # 读取已有文件，首列为行索引（品牌）
        existing_df = pd.read_excel(output_path, index_col=0)
        existing_df.index.name = "品牌"
        existing_df.columns = [str(c) for c in existing_df.columns]

        # 仅挑选新数据中在旧文件里不存在的月份列
        new_cols = [c for c in pivot_df.columns if c not in existing_df.columns]
        if new_cols:
            merged_df = existing_df.join(pivot_df[new_cols], how="left")
        else:
            merged_df = existing_df

        # 列按年月排序（无法解析为日期的列保持原序在末尾）
        def sort_columns_chronologically(columns: pd.Index) -> list:
            col_series = pd.Series(list(columns))
            parsed = pd.to_datetime(col_series, format="%Y-%m", errors="coerce")
            # 可解析的先按日期排序，NaT 的放在最后并保持原相对顺序
            sortable = col_series[parsed.notna()].tolist()
            not_sortable = col_series[parsed.isna()].tolist()
            sortable_sorted = sorted(sortable, key=lambda x: pd.to_datetime(x, format="%Y-%m"))
            return sortable_sorted + not_sortable

        merged_df = merged_df[sort_columns_chronologically(merged_df.columns)]
        merged_df.to_excel(output_path)
        print(f"已补充并保存 Excel：{output_path}")
    except Exception as e:
        # 回退方案：如读取失败，直接覆盖写入
        pivot_df.to_excel(output_path)
        print(f"读取现有文件失败，已直接保存新数据：{output_path}，错误：{e}")
else:
    pivot_df.to_excel(output_path)
    print(f"已保存为 Excel 文件：{output_path}")
