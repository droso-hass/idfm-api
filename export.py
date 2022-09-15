import requests
import json

LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"
STOP_AND_LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/arrets-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"

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

line_to_stops = {}
for i in requests.get(STOP_AND_LINES).json():
    id = i["fields"]["id"].split(":")[1]
    if id not in line_to_stops:
        if id in line_ids:
            line_to_stops[id] = []
    else:
        line_to_stops[id].append({
            "id": i["fields"]["id"],
            "stop_id": i["fields"]["stop_id"],
            "name": i["fields"]["stop_name"],
            "city": i["fields"]["nom_commune"],
            "zipCode": i["fields"]["code_insee"],
            "x": i["fields"]["stop_lat"],
            "y": i["fields"]["stop_lon"],
        })

with open("idfm_api/lines.json", "w", encoding="utf8") as f:
    json.dump(lines, f, ensure_ascii=False)


with open("idfm_api/stops.json", "w", encoding="utf8") as f:
    json.dump(line_to_stops, f, ensure_ascii=False)