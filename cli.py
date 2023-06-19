from idfm_api import IDFMApi
from idfm_api.models import TransportType
import asyncio
import aiohttp

async def main():
    session = aiohttp.ClientSession()
    apikey = input("Enter API KEY:")
    idfm = IDFMApi(session, apikey)

    lines = await idfm.get_lines(TransportType.TRAIN)
    for i, val in enumerate(lines):
        print(f"#{i} - {val.name}")
    line = lines[int(input("Select line "))]

    print("\n")
    stops = await idfm.get_stops(line.id)
    for i, val in enumerate(stops):
        print(f"#{i} - {val.name}")
    stop = stops[int(input("Select stop area "))]
    stop_id = stop.exchange_area_id or stop.stop_id

    print("\n")
    directions = await idfm.get_destinations(stop_id, line_id=line.id)
    for i, val in enumerate(directions):
        print(f"#{i} - {val}")
    d = input("Select direction (leave blank to display all) ")
    dir = None if d == "" else directions[int(d)]

    print("\n")
    print("Traffic:")
    for i in await idfm.get_traffic(stop_id, destination_name=dir, line_id=line.id):
        print(f"Line {i.line_id} {i.note} - Destination {i.destination_name}: {i.schedule} - Currently at stop: {i.at_stop} - Platform: {i.platform} - Status: {i.status}") 
        
    print("\n")
    print("Informations:")
    for i in await idfm.get_infos(line.id):
        print(f"{i.name} - Type {i.type} - Severity {i.severity}\nStart {i.start_time} - End {i.end_time}\n{i.message}")

    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
