import requests
from idfm_api.models import LineData, StopData, TrafficData, InfoData, TransportType
from typing import List, Optional
import json
import importlib.resources

BASE_URL = "https://api-iv.iledefrance-mobilites.fr/lines/"

def __request(url):
    data = requests.get(url)
    if data.status_code != 200:
        raise Exception(f"invalid status code returned: {data.status_code}")
    return data.json()

def get_stops(line_id: str) -> List[StopData]:
    """
    Return a list of stop areas corresponding to the specified line
    Args:
        line_id: A string indicating id of a line
    Returns:
        A list of StopData objects
    """
    data = __request(f"{BASE_URL}{line_id}/stops?stopPoints=false&routes=false")
    ret = []
    for i in data:
        ret.append(StopData.from_json(i))
    return ret

def get_traffic(line_id: str, stop_id: str, direction_name: Optional[str] = None, forward: Optional[bool] = None) -> List[TrafficData]:
    """
    Returns the next schedules in a line for a specified depart area to an optional destination
    
    Args:
        line_id: A string representing the id of a line
        stop_id: A string indicating the id of the depart stop area
        direction_name: A string indicating the final destination (I.E. the station name returned by get_directions), the schedules for all the available destinations are returned if not specified
        forward: A boolean indicating the direction of a train (forward/backward), ignored if not specified
    Returns:
        A list of TrafficData objects
    """
    data = __request(f"{BASE_URL}{line_id}/stops/{stop_id}/realTime")
    ret = []
    for i in data:
        d = TrafficData.from_json(i)
        if (direction_name is None or d.direction == direction_name) and (forward is None or d.forward == forward):
            ret.append(d)
    return sorted(ret)

def get_directions(line_id: str, forward: Optional[bool] = None) -> List[str]:
    """
    Returns the available destinations for a specified line

    Args:
        line_id: A string indicating the id of a line
        forward: A boolean indicating the direction of a train
    Returns:
        A list of string representing the stations names
    """
    ret = set()
    for i in get_traffic(line_id, get_stops(line_id)[0].id, forward=forward):
        ret.add(i.direction)
    return list(ret)

def get_infos(line_id: str) -> List[InfoData]:
    """
    Returns the traffic informations (usually the current/planned perturbations) for the specified line
    
    Args:
        line_id: A string indicating the id of a line
    Returns:
        A list of InfoData objects, the list is empty if no perturbations are registered
    """
    ret = []
    data = __request(f"{BASE_URL}{line_id}/schedules?complete=false")
    if "currentIT" in data:
        for i in data["currentIT"]:
            ret.append(InfoData.from_json(i))
    return ret

def get_lines(transport: Optional[TransportType] = None) -> List[LineData]:
    """
    Returns the available lines by transport type

    Args:
        transport: the transport type, all of them are returned if this is omitted
    Returns:
        A list of LineData objects
    """
    ret = []
    #with open("lines.json", "r", encoding="utf8") as f:
    with importlib.resources.open_text("idfm_api", "lines.json", encoding="utf8") as f:
        data = json.load(f)
        for i in data.keys():
            if transport is None or transport.value == i:
                for name, id in data[i].items():
                    ret.append(LineData(name=name, id=id, type=TransportType(i)))
    return ret
