| 欄位名稱                      | 型態     | 說明                            
| ---------------------------- | -------- | ----------------------------- 
| `id`                         | string   | CCTV 唯一識別碼                    
| `location`                   | string   | CCTV 所在路段名稱                   
| `lat`                        | float    | 緯度                            
| `lng`                        | float    | 經度                            
| `snapshot_url`               | string   | CCTV 快照圖片或影像串流 URL            
| `rain_summary`               | dict     | 6 公里範圍內雨量測站的最大值與平均值統計         
| `rain_distance_weighted_1hr` | float    | 距離加權的過去 1 小時雨量平均值 (mm)        
| `realtime_rain`              | float    | 最近雨量測站的過去 1 小時雨量 (mm)         
| `rain_station_id`            | string   | 最近雨量測站 ID                     
| `rain_distance_km`           | float    | 最近雨量測站距離 CCTV 的公里數            
| `nearby_segments`            | list     | 300 公尺內鄰近的其他 CCTV 路段清單        
| `risk_level`                 | string   | 風險等級（normal, warning, danger） 
| `status`                     | string   | 狀態（預設 normal）                 
| `road_event`                 | nullable | 預留欄位，後續整合道路事件資料               
| `risk_score`                 | float    | 動態風險分數（0-100）                 
| `last_update`                | string   | 最後資料更新時間 ISO 格式字串             
