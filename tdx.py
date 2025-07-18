import requests
import json
from collections import defaultdict

app_id = 's12350105-b97b401b-d470-40cd'
app_key = 'b9b60d2f-8dfa-420d-980a-d4d52d5d2e42'

auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
url = "https://tdx.transportdata.tw/api/basic/v1/Traffic/RoadEvent/LiveEvent/City/Taichung?$top=50&$format=JSON"

# --------- 經緯度解析 ---------
def extract_lat_lng(position_str):
    try:
        if not position_str.startswith("POINT"):
            return None, None
        coords = position_str.replace("POINT (", "").replace(")", "").split()
        lng, lat = float(coords[0]), float(coords[1])
        return lat, lng
    except:
        return None, None

class Auth():
    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_response(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.app_id,
            'client_secret': self.app_key
        }
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        return response

class Data():
    def __init__(self, access_token):
        self.access_token = access_token

    def get_data_header(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept-Encoding': 'gzip'
        }

def classify_events(events):
    classified = defaultdict(list)
    for e in events:
        etype = e.get('EventType', '未知')
        classified[etype].append(e)
    return classified

event_type_map = {
    1: '交通事故',
    2: '道路施工',
    3: '壅塞',
}

if __name__ == '__main__':
    a = Auth(app_id, app_key)
    auth_response = a.get_auth_response()
    access_token = auth_response.json().get('access_token')
    print(f"✅ Token 取得成功，狀態碼 {auth_response.status_code}")

    d = Data(access_token)
    data_response = requests.get(url, headers=d.get_data_header())
    data_response.raise_for_status()
    print(f"✅ RoadEvent 取得成功，狀態碼 {data_response.status_code}")

    json_data = data_response.json()
    events = json_data.get('LiveEvents', [])

    for e in events:
        lat, lng = extract_lat_lng(e.get("Positions", ""))
        e["lat"] = lat
        e["lng"] = lng
        e.pop("Positions", None)

    with open("road_event.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"✅ RoadEvent 共 {len(events)} 筆，已儲存 road_event.json")
