import requests
from idfm_api.exceptions import APIException
from idfm_api.models import LineData, StopData, TrafficData, InfoData, TransportType
from typing import List, Optional
import json
import importlib.resources

BASE_URL = "https://api-iv.iledefrance-mobilites.fr/lines/"

def __request(url):
    data = requests.get(url)
    if data.status_code != 200:
        raise APIException(f"invalid status code returned: {data.status_code}")
    return data.json()

def get_stops(line_id: str) -> List[StopData]:
    data = __request(f"{BASE_URL}{line_id}/stops?stopPoints=false&routes=false")
    ret = []
    for i in data:
        ret.append(StopData.from_json(i))
    return ret

def get_traffic(line_id: str, stop_id: str, direction_name: Optional[str] = None, forward: Optional[bool] = None) -> List[TrafficData]:
    data = __request(f"{BASE_URL}{line_id}/stops/{stop_id}/realTime")
    ret = []
    for i in data:
        d = TrafficData.from_json(i)
        if (direction_name is None or d.direction == direction_name) and (forward is None or d.forward == forward):
            ret.append(d)
    return sorted(ret)

def get_directions(line_id: str, forward: Optional[bool] = None) -> List[str]:
    ret = set()
    for i in get_traffic(line_id, get_stops(line_id)[0].id, forward=forward):
        ret.add(i.direction)
    return list(ret)

def get_infos(line_id: str) -> List[InfoData]:
    ret = []
    data = __request(f"{BASE_URL}{line_id}/schedules?complete=false")
    if "currentIT" in data:
        for i in data["currentIT"]:
            ret.append(InfoData.from_json(i))
    return ret

def get_lines(transport: Optional[TransportType] = None) -> List[LineData]:
    ret = []
    #with open("lines.json", "r", encoding="utf8") as f:
    with importlib.resources.open_text("idfm_api", "lines.json", encoding="utf8") as f:
        data = json.load(f)
        for i in data.keys():
            if transport is None or transport.value == i:
                for name, id in data[i].items():
                    ret.append(LineData(name=name, id=id, type=TransportType(i)))
    return ret
