from idfm_api import IDFMApi
from idfm_api.models import TransportType
import asyncio
import aiohttp

async def main():
    session = aiohttp.ClientSession()
    idfm = IDFMApi(session)

    lines = await idfm.get_lines(TransportType.METRO)
    for i, val in enumerate(lines):
        print(f"#{i} - {val.name}")
    line = lines[int(input("Select line "))]

    print("\n")
    stops = await idfm.get_stops(line.id)
    for i, val in enumerate(stops):
        print(f"#{i} - {val.name}")
    stop = stops[int(input("Select stop area "))]

    print("\n")
    directions = await idfm.get_directions(line.id, stop.id)
    for i, val in enumerate(directions):
        print(f"#{i} - {val}")
    d = input("Select direction (leave blank to display all) ")
    dir = None if d == "" else directions[int(d)]

    print("\n")
    print("Traffic:")
    for i in await idfm.get_traffic(line.id, stop.id, dir):
        print(f"Line {i.short_name} - Direction {i.direction}: {i.schedule}") 

    print("\n")
    print("Informations:")
    for i in await idfm.get_infos(line.id):
        print(f"{i.name} - Type {i.type} - Severity {i.severity.value}\nStart {i.start_time} - End {i.end_time}\n{i.message}")

    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())