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
def summarize_rain(subset, cols=("Now","Past1hr","Past3hr","Past24hr")):
    if subset.empty:
        return pd.Series(dtype=float)
    stats = {}
    for c in cols:
        vals = pd.to_numeric(subset[c], errors="coerce").dropna()
        stats[f"{c}_max"] = round(vals.max(), 2) if not vals.empty else None
        stats[f"{c}_mean"] = round(vals.mean(), 2) if not vals.empty else None
    return pd.Series(stats)

# --------- 距離加權平均 ----------
def distance_weighted_mean(subset, col="Past1hr", min_weight_dist=0.1):
    if subset.empty:
        return None
    vals = pd.to_numeric(subset[col], errors="coerce")
    d = subset["Distance_km"].clip(lower=min_weight_dist)
    w = 1 / d
    return round((vals * w).sum() / w.sum(), 2)

# --------- 主程式 ---------
cctv_df = pd.read_csv("臺中市交通即時道路影像.csv")
rain_df = pd.read_csv("rainfall_detailed.csv")

cctv_list = []
for _, row in cctv_df.iterrows():
    if pd.isna(row["py"]) or pd.isna(row["px"]):
        continue

    lat, lng = float(row["py"]), float(row["px"])
    nearby_rains = stations_in_radius(rain_df, lat, lng, radius_km=5)

    rain_summary = summarize_rain(nearby_rains).to_dict()
    rain_weighted_1hr = distance_weighted_mean(nearby_rains)

    # nearby CCTV (300m)
    nearby_segments = []
    for _, other in cctv_df.iterrows():
        if row["cctvid"] == other["cctvid"] or pd.isna(other["py"]) or pd.isna(other["px"]):
            continue
        dist_m = geodesic((lat, lng), (float(other["py"]), float(other["px"]))).meters
        if dist_m <= 300:
            nearby_segments.append({
                "id": str(other["cctvid"]).strip(),
                "location": other["roadsection"],
                "snapshot_url": other["url"].strip(),
                "distance_m": round(dist_m, 1)
            })

    risk_level = "danger" if rain_weighted_1hr and rain_weighted_1hr >= 10 else \
                 "warning" if rain_weighted_1hr and rain_weighted_1hr >= 5 else "normal"

    cctv = {
        "id": str(row["cctvid"]).strip(),
        "location": row["roadsection"],
        "lat": lat,
        "lng": lng,
        "snapshot_url": row["url"].strip(),
        "rain_summary": rain_summary,
        "rain_distance_weighted_1hr": rain_weighted_1hr,
        "nearby_segments": sorted(nearby_segments, key=lambda x: x["distance_m"]),
        "risk_level": risk_level,
        "last_update": datetime.now().isoformat()
    }

    cctv_list.append(cctv)

print(f"✅ 總計 {len(cctv_list)} 筆 CCTV 完成整合")

with open("taichung_cctv_with_rain_summary.json", "w", encoding="utf-8") as f:
    json.dump(cctv_list, f, ensure_ascii=False, indent=2)
