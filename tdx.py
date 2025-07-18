import requests
from pprint import pprint
import json
from collections import defaultdict

app_id = 's12350105-b97b401b-d470-40cd'
app_key = 'b9b60d2f-8dfa-420d-980a-d4d52d5d2e42'

auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
url = "https://tdx.transportdata.tw/api/basic/v1/Traffic/RoadEvent/LiveEvent/City/Taichung?$top=50&$format=JSON"

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

def print_events_summary(json_data):
    events = json_data.get('LiveEvents', [])
    classified_events = classify_events(events)

    print(f"更新時間：{json_data.get('UpdateTime')}")
    print(f"資料更新頻率：{json_data.get('UpdateInterval')}秒")
    print(f"共取得事件數量：{len(events)}\n")

    print("事件分類統計：")
    for etype, evlist in classified_events.items():
        etype_name = event_type_map.get(etype, f'未知類型({etype})')
        print(f"  - {etype_name}: {len(evlist)} 筆")

    print("\n詳細事件列表：")
    for etype, evlist in classified_events.items():
        etype_name = event_type_map.get(etype, f'未知類型({etype})')
        print(f"\n== {etype_name} ==")
        for e in evlist:
            print(f"事件ID: {e.get('EventID')}")
            print(f"標題: {e.get('EventTitle')}")
            print(f"描述: {e.get('Description')}")
            print(f"時間: {e.get('EffectiveTime')}")
            print(f"地點: {e.get('Location', {}).get('Other', '無')}")
            print("-" * 40)

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
    print_events_summary(json_data)
