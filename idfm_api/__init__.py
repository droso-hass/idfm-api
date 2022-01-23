from idfm_api.models import LineData, StopData, TrafficData, InfoData, TransportType
from typing import List, Optional
import json
import logging
import importlib.resources
import aiohttp
import async_timeout
import asyncio

BASE_URL = "https://api-iv.iledefrance-mobilites.fr/lines/"
TIMEOUT = 10
_LOGGER: logging.Logger = logging.getLogger(__package__)

class IDFMApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def __request(self, url):
        """
        API request helper
        Args:
            url: the url to request
        Returns:
            A json object
        """
        try:
            async with async_timeout.timeout(TIMEOUT):
                response = await self._session.get(url)
                if response.status != 200:
                    _LOGGER.error(
                        "Error while fetching information from %s - %s",
                        url,
                        response._body,
                    )
                return await response.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)

    async def get_stops(self, line_id: str) -> List[StopData]:
        """
        Return a list of stop areas corresponding to the specified line
        Args:
            line_id: A string indicating id of a line
        Returns:
            A list of StopData objects
        """
        data = await self.__request(f"{BASE_URL}{line_id}/stops?stopPoints=false&routes=false")
        ret = []
        for i in data:
            ret.append(StopData.from_json(i))
        return ret

    async def get_traffic(self, line_id: str, stop_id: str, direction_name: Optional[str] = None, forward: Optional[bool] = None) -> List[TrafficData]:
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
        data = (await self.__request(f"{BASE_URL}{line_id}/stops/{stop_id}/realTime"))["nextDepartures"]["data"]
        ret = []
        for i in data:
            d = TrafficData.from_json(i)
            if (direction_name is None or d.direction == direction_name) and (forward is None or d.forward == forward):
                ret.append(d)
        return sorted(ret)

    async def get_directions(self, line_id: str, forward: Optional[bool] = None) -> List[str]:
        """
        Returns the available destinations for a specified line

        Args:
            line_id: A string indicating the id of a line
            forward: A boolean indicating the direction of a train
        Returns:
            A list of string representing the stations names
        """
        ret = set()
        for i in await self.get_traffic(line_id, (await self.get_stops(line_id))[0].id, forward=forward):
            ret.add(i.direction)
        return list(ret)

    async def get_infos(self, line_id: str) -> List[InfoData]:
        """
        Returns the traffic informations (usually the current/planned perturbations) for the specified line
        
        Args:
            line_id: A string indicating the id of a line
        Returns:
            A list of InfoData objects, the list is empty if no perturbations are registered
        """
        ret = []
        data = await self.__request(f"{BASE_URL}{line_id}/schedules?complete=false")
        if "currentIT" in data:
            for i in data["currentIT"]:
                ret.append(InfoData.from_json(i))
        return ret

    async def get_lines(self, transport: Optional[TransportType] = None) -> List[LineData]:
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
