import requests
from bs4 import BeautifulSoup
import os
import json

BASE_URL = "https://me-deplacer.iledefrance-mobilites.fr/fiches-horaires/"
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

data = {}
for i in items:
    data[i] = get_lines(i)

with open("idfm-api/lines.json", "w", encoding="utf8") as f:
    json.dump(data, f, ensure_ascii=False)