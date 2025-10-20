import akshare as ak
import pandas as pd
from datetime import datetime

# ====== 参数设置 ======
start_date = "20250101"
end_date = datetime.today().strftime("%Y%m%d")

# ====== 获取交易日列表 ======
trade_dates = ak.tool_trade_date_hist_sina()
trade_dates["trade_date"] = pd.to_datetime(trade_dates["trade_date"]).dt.strftime("%Y%m%d")
trade_dates = trade_dates[
    (trade_dates["trade_date"] >= start_date) & 
    (trade_dates["trade_date"] <= end_date)
]
date_list = trade_dates["trade_date"].tolist()

# ====== 逐日获取首板数据 stock_zt_pool_em只有最近一个月数据======
all_data = []

for date in date_list:
    try:
        df = ak.stock_zt_pool_em(date=date)
        if df is not None and not df.empty:
            print(df)
            df = df[df["连板数"] == 1].copy()
            df["日期"] = date
            df["是否炸板"] = df["炸板次数"].apply(lambda x: "是" if x > 0 else "否")
            if "涨停封单额" in df.columns:
                df.rename(columns={"涨停封单额": "封板资金"}, inplace=True)
            elif "封单资金" in df.columns:
                df.rename(columns={"封单资金": "封板资金"}, inplace=True)
            else:
                df["封板资金"] = None

            if "涨停原因类别" not in df.columns:
                df["涨停原因类别"] = None

            all_data.append(df[[
                "日期", "代码", "名称", "换手率","成交额", "流通市值","首次封板时间","最后封板时间","涨跌幅", "炸板次数", "是否炸板",
                "封板资金", "所属行业", "涨停原因类别"
            ]])
        print(f"{date} 完成,首板数: {len(df)}")
    except Exception as e:
        print(f"{date} 出错: {e}")

# ====== 合并与保存 ======
if all_data:
    result = pd.concat(all_data, ignore_index=True)
    result.to_csv("A股首板_2025.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ 已保存到 A股首板_2025.csv,共 {len(result)} 条记录。")
else:
    print("❌ 未获取到数据,请检查网络或接口状态。")