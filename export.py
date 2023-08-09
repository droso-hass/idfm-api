import requests
import json

"""
Export Script used to generate lines.json and stops.json

The first file contains a list of all the lines id for each transport category
The second contains a mapping of the line id to a list of all the stops for this line

To find a list of all the stops we need to use multiple datasets:
LINES
 -> get line ID
 -> STOP_AND_LINES -> get corresponding stops areas for trains (ZdAId) OR get corresponding stops points for other modes (ArRId)
 -> STOP_RELATIONS -> map the ArRid to ZdAId AND map the ZdAId to the exchange area (ZdCId) 
 -> EXCHANGE_AREAS -> get the exchange area data

So the process looks like this: LineID -> ZdAId -> ZdCId OR LineID -> ArId -> ZdAId -> ZdCId
"""

LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"
STOP_AND_LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/arrets-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"
STOP_RELATIONS = "https://data.iledefrance-mobilites.fr/explore/dataset/relations/download/?format=json&timezone=Europe/Berlin&lang=fr"
EXCHANGE_AREAS = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/zones-de-correspondance/exports/json?lang=fr&timezone=Europe/Berlin"

lines = {}
line_ids = []
for l in requests.get(LINES).json():
    mode = l["fields"]["transportmode"]
    if mode not in lines:
        lines[mode] = {}

    name = l["fields"]["name_line"]
    if mode == "bus" and "operatorname" in l["fields"]:
        name += " / " + l["fields"]["operatorname"]

    lines[mode][name] = l["fields"]["id_line"]
    line_ids.append(l["fields"]["id_line"])

arid_to_zdaid = {}
zdaid_to_zdcid = {}
for i in requests.get(STOP_RELATIONS).json():
    try:
        arid_to_zdaid[i["fields"]["arrid"]] = i["fields"]["zdaid"]
    except KeyError:
        pass
    try:
        zdaid_to_zdcid[i["fields"]["zdaid"]] = i["fields"]["zdcid"]
    except KeyError:
        pass

zdc = {}
for i in requests.get(EXCHANGE_AREAS).json():
    zdc[i["zdcid"]] = i

# map line to stops
line_to_stops = {}
stop_ids = {}
for i in requests.get(STOP_AND_LINES).json():
    id = i["fields"]["id"].split(":")[1]
    if id not in line_to_stops:
        line_to_stops[id] = []
        stop_ids[id] = []

    if id in line_ids:
        stop_id = i["fields"]["stop_id"]
        if stop_id.find("monomodalStopPlace") == -1:
            try:
                stop_id = arid_to_zdaid[stop_id.split(":")[-1]]
            except KeyError:
                pass
        else:
            stop_id = stop_id[24:]

        # try to find the corresponding Exchange Area ID (ZdCId)
        zdcid = zdaid_to_zdcid.get(stop_id)
        
        if stop_id not in stop_ids[id]:
            line_to_stops[id].append({
                "exchange_area_id": None if zdcid is None else "STIF:StopArea:SP:"+zdcid+":",
                "exchange_area_name": None if zdcid is None else zdc[zdcid]["zdcname"],
                "stop_id": "STIF:StopPoint:Q:"+stop_id+":",
                "name": i["fields"]["stop_name"],
                "city": i["fields"]["nom_commune"],
                "zipCode": i["fields"]["code_insee"],
                "x": i["fields"]["stop_lat"],
                "y": i["fields"]["stop_lon"],
            })
            stop_ids[id].append(stop_id)

# remove lines with no associated stops
filtered_lines = {}
for mode, data in lines.items():
    for name, value in data.items():
        if value in line_to_stops:
            if mode not in filtered_lines:
                filtered_lines[mode] = {}
            filtered_lines[mode][name] = value

with open("idfm_api/lines.json", "w", encoding="utf8") as f:
    json.dump(filtered_lines, f, ensure_ascii=False)


with open("idfm_api/stops.json", "w", encoding="utf8") as f:
    json.dump(line_to_stops, f, ensure_ascii=False)