import pandas as pd
import json
from geopy.distance import geodesic
from datetime import datetime

# --------- geopy 計算距離 (km) ----------
def haversine_km(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).km

# --------- 找範圍內觀測站 ----------
def stations_in_radius(df, lat, lon, radius_km):
    tmp = df.copy()
    tmp["Distance_km"] = tmp.apply(
        lambda r: haversine_km(lat, lon, float(r["Latitude"]), float(r["Longitude"])),
        axis=1
    )
    return tmp.loc[tmp["Distance_km"] <= radius_km].sort_values("Distance_km")

# --------- 統計雨量 ----------
def summarize_rain(subset, cols=("Now", "Past1hr", "Past3hr", "Past24hr")):
    stats = {}
    for c in cols:
        vals = pd.to_numeric(subset[c], errors="coerce").dropna()
        stats[f"{c}_max"] = round(vals.max(), 2) if not vals.empty else 0.0
        stats[f"{c}_mean"] = round(vals.mean(), 2) if not vals.empty else 0.0
    return stats

# --------- 距離加權平均 ----------
def distance_weighted_mean(subset, col="Past1hr", min_weight_dist=0.1):
    if subset.empty:
        return 0.0
    vals = pd.to_numeric(subset[col], errors="coerce").fillna(0)
    d = subset["Distance_km"].clip(lower=min_weight_dist)
    w = 1 / d
    return round((vals * w).sum() / w.sum(), 2)

# --------- 主程式 ---------
# 讀取資料
cctv_df = pd.read_csv("臺中市交通即時道路影像.csv")
rain_df = pd.read_csv("rainfall_detailed.csv")

# 數值正規化處理
for col in ["Past1hr", "Past3hr", "Past24hr", "Now"]:
    rain_df[col] = pd.to_numeric(rain_df[col], errors="coerce").fillna(0).round(2)

# 預處理 CCTV
cctv_list = []
for _, row in cctv_df.iterrows():
    if pd.isna(row["py"]) or pd.isna(row["px"]):
        continue
    lat, lng = float(row["py"]), float(row["px"])

    # 找範圍內雨量站
    nearby_rains = stations_in_radius(rain_df, lat, lng, radius_km=6)

    cctv = {
        "id": str(row["cctvid"]).strip(),
        "location": row["roadsection"],
        "lat": lat,
        "lng": lng,
        "snapshot_url": row["url"].strip(),
        "risk_level": "normal",
        "status": "normal",
        "risk_score": 0,
        "realtime_rain": 0.0,
        "rain_summary": summarize_rain(nearby_rains),
        "rain_distance_weighted_1hr": distance_weighted_mean(nearby_rains, col="Past1hr"),
        "road_event": {
            "event_id": None,
            "event_type": None,
            "event_level": None,
            "distance_km": None
        },
        "nearby_segments": []
    }

    """
    cctv = {
    "id": str(row["cctvid"]).strip(),   # CCTV 編號（唯一識別碼）
    "location": row["roadsection"],     # CCTV 所在路段名稱
    "lat": lat,                        # CCTV 緯度
    "lng": lng,                        # CCTV 經度
    "snapshot_url": row["url"].strip(),# CCTV URL

    # CCTV 附近 6 公里範圍內的雨量統計摘要
    "rain_summary": {                   # 以雨量測站資料統計出的最大值與平均值
        "Now_max": ...,                 # 當前雨量最大值
        "Now_mean": ...,                # 當前雨量平均值
        "Past1hr_max": ...,             # 過去1小時雨量最大值
        "Past1hr_mean": ...,            # 過去1小時雨量平均值
        "Past3hr_max": ...,             # 過去3小時雨量最大值
        "Past3hr_mean": ...,            # 過去3小時雨量平均值
        "Past24hr_max": ...,            # 過去24小時雨量最大值
        "Past24hr_mean": ...,           # 過去24小時雨量平均值
    },
    "rain_distance_weighted_1hr": ..., # 以距離加權的過去1小時雨量平均值 (km級距離權重)

    "realtime_rain": float,            # 最近雨量測站的過去1小時雨量(mm)
    "rain_station_id": str,            # 最近雨量測站ID
    "rain_distance_km": float,         # 最近雨量測站距離 CCTV 的公里數

    "nearby_segments": [                # 300公尺內鄰近的其他 CCTV 路段清單
        {
            "id": str,                  # 鄰近 CCTV ID
            "location": str,            # 鄰近 CCTV 路段名稱
            "snapshot_url": str,        # 鄰近 CCTV 快照 URL
            "distance_m": float         # 與該 CCTV 的距離（公尺）
        },
        ...
    ],

    "risk_level": str,                 # 風險等級（"normal", "warning", "danger"）
    "status": str,                    # 目前狀態，一般為 "normal"
    
    "road_event": None,               # 預留欄位，道路事件資料
    
    "risk_score": float            # 動態風險分數，範圍 0-100（可後續計算加權）
}
    """

    # 最近雨量站距離
    if not nearby_rains.empty:
        nearest_rain = nearby_rains.iloc[0]
        cctv["realtime_rain"] = round(float(nearest_rain["Past1hr"]), 2)
        cctv["rain_station_id"] = nearest_rain["StationId"]
        cctv["rain_distance_km"] = round(float(nearest_rain["Distance_km"]), 2)

    # 風險判斷(temp)
    rain = cctv["realtime_rain"]
    if rain >= 10:
        cctv["risk_level"] = "danger"
        cctv["risk_score"] = min(100, round(rain * 8, 0))
    elif rain >= 5:
        cctv["risk_level"] = "warning"
        cctv["risk_score"] = min(80, round(rain * 6, 0))
    else:
        cctv["risk_level"] = "normal"
        cctv["risk_score"] = min(50, round(rain * 5, 0))

    # 鄰近段落
    nearby = []
    for _, other in cctv_df.iterrows():
        if row["cctvid"] == other["cctvid"] or pd.isna(other["py"]) or pd.isna(other["px"]):
            continue
        dist = geodesic((lat, lng), (other["py"], other["px"])).meters
        if dist <= 300:
            nearby.append({
                "id": str(other["cctvid"]).strip(),
                "location": other["roadsection"],
                "snapshot_url": other["url"].strip(),
                "distance_m": round(dist, 1)
            })
    cctv["nearby_segments"] = sorted(nearby, key=lambda x: x["distance_m"])

    cctv_list.append(cctv)

print(f"✅ 總計 {len(cctv_list)} 筆 CCTV 完成整合")

with open("cctv_with_rain_riskevent.json", "w", encoding="utf-8") as f:
    json.dump(cctv_list, f, ensure_ascii=False, indent=2)
