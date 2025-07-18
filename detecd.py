import pandas as pd
from geopy.distance import geodesic

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
        if vals.empty:
            stats[c+"_max"] = float("nan")
            stats[c+"_mean"] = float("nan")
            continue
        stats[c+"_max"] = vals.max()
        stats[c+"_mean"] = vals.mean()
    return pd.Series(stats)

# --------- 距離加權平均 ----------
def distance_weighted_mean(subset, col="Past1hr", min_weight_dist=0.1):
    if subset.empty:
        return float("nan")
    vals = pd.to_numeric(subset[col], errors="coerce")
    d = subset["Distance_km"].clip(lower=min_weight_dist)
    w = 1 / d
    return (vals * w).sum() / w.sum()



if __name__ == "__main__":
    # 讀取觀測站資料
    df = pd.read_csv("rainfall_detailed.csv")

    # 測試座標
    lat, lon = 24.1824738,120.5999671 #(東海)
    radius_km = 6

    nearby = stations_in_radius(df, lat, lon, radius_km)
    print("找到", len(nearby), "個觀測站在", radius_km, "公里內")
    print(nearby[["StationName","Town","Distance_km","Now","Past1hr","Past3hr","Past24hr"]])

    if nearby.empty:
        print("附近無觀測站")
    else:
        summary = summarize_rain(nearby)
        print("\n統計：")
        print(summary)

        dwm = distance_weighted_mean(nearby, col="Past1hr")
        print(f"\n距離加權平均 Past1hr 雨量：{dwm:.2f} mm")
