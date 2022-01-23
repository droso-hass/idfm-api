import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://me-deplacer.iledefrance-mobilites.fr/fiches-horaires/"
BUS_URL = "https://api-iv.iledefrance-mobilites.fr/lines?q="
items = ["train", "metro", "tramway"]

def get_lines(transport):
    ret = {}
    raw = requests.get(BASE_URL+transport).text
    soup = BeautifulSoup(raw, features="html.parser")
    resp = soup.find_all("a", {"class":"heading-block-transport-timetable"})
    for i in resp:
        link = i.attrs["href"]
        ret[i.contents[1].getText()] = link[18+len(transport):link.find("?")].replace("%3A", ":")
    return ret

def get_bus_lines():
    lines = set()
    for i in range(1,99):
        for j in requests.get(BUS_URL + str(i)).json():
            lines.add((f"{j['label']} - {j['network']['label']}", j["id"]))
        time.sleep(0.5)

    ret = {}
    for i in lines:
        ret[i[0]] = i[1]
    return ret

data = {}
for i in items:
    data[i] = get_lines(i)
data["bus"] = get_bus_lines()

with open("idfm_api/lines.json", "w", encoding="utf8") as f:
    json.dump(data, f, ensure_ascii=False)