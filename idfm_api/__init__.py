from idfm_api.models import LineData, StopData, TrafficData, InfoData, TransportType
from typing import List, Optional
import json
import logging
import importlib.resources
import aiohttp
import async_timeout
import asyncio

TIMEOUT = 60
_LOGGER: logging.Logger = logging.getLogger(__package__)

class IDFMApi:
    def __init__(self, session: aiohttp.ClientSession, apikey: str, timeout: int = TIMEOUT) -> None:
        self._session = session
        self._apikey = apikey
        self._timeout = timeout

    async def __request(self, url):
        """
        API request helper
        Args:
            url: the url to request
        Returns:
            A json object
        """
        try:
            async with async_timeout.timeout(self._timeout):
                response = await self._session.get(url, headers={
                    "apiKey": self._apikey,
                    "Content-Type": "application/json",
                    "Accept-encoding": "gzip, deflate"
                })
                if response.status != 200:
                    _LOGGER.debug(
                        "Error while fetching information from %s - %s",
                        url,
                        response._body,
                    )
                resp = (await response.json())["Siri"]["ServiceDelivery"]
                if "GeneralMessageDelivery" in resp:
                    resp = resp["GeneralMessageDelivery"][0]
                elif "StopMonitoringDelivery" in resp:
                    resp = resp["StopMonitoringDelivery"][0]

                if resp["Status"] == "false":
                    _LOGGER.debug(
                        "Error while fetching information from %s - %s",
                        url,
                        response._body,
                    )
                    return None
                    
                return resp

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
        ret = []
        with importlib.resources.open_text("idfm_api", "stops.json", encoding="utf8") as f:
            data = json.load(f)
            if line_id in data:
                for i in data[line_id]:
                    ret.append(StopData.from_json(i))
        return ret

    async def get_traffic(self, stop_id: str, destination_name: Optional[str] = None, direction_name: Optional[str] = None) -> List[TrafficData]:
        """
        Returns the next schedules in a line for a specified depart area to an optional destination
        
        Args:
            stop_id: A string indicating the id of the depart stop area
            destination_name: A string indicating the final destination (I.E. the station name returned by get_directions), the schedules for all the available destinations are returned if not specified
            direction_name: A boolean indicating the direction of a train, ignored if not specified
        Returns:
            A list of TrafficData objects
        """
        d = f"https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring?MonitoringRef=STIF:StopPoint:Q:{stop_id.split(':')[-1]}:"
        data = (await self.__request(d))["MonitoredStopVisit"]
        ret = []
        for i in data:
            d = TrafficData.from_json(i)
            if d and (direction_name is None or d.direction == direction_name) and (destination_name is None or d.destination_name == destination_name):
                ret.append(d)
        return sorted(ret)

    async def get_destinations(self, stop_id: str, direction_name: Optional[str] = None) -> List[str]:
        """
        Returns the available destinations for a specified line

        Args:
            stop_id: A string indicating the id of the depart stop area
            direction_name: The direction of a train
        Returns:
            A list of string representing the stations names
        """
        ret = set()
        for i in await self.get_traffic(stop_id, direction_name=direction_name):
            ret.add(i.destination_name)
        return list(ret)

    async def get_directions(self, stop_id: str) -> List[str]:
        """
        Returns the available directions for a specified line

        Args:
            stop_id: A string indicating the id of the depart stop area
        Returns:
            A list of string representing the stations names
        """
        ret = set()
        for i in await self.get_traffic(stop_id):
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
        data = await self.__request(f"https://prim.iledefrance-mobilites.fr/marketplace/general-message?LineRef=STIF:Line::{line_id}:")
        if data:
            for i in data["InfoMessage"]:
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
        with importlib.resources.open_text("idfm_api", "lines.json", encoding="utf8") as f:
            data = json.load(f)
            if transport.value in data:
                for name, id in data[transport.value].items():
                    ret.append(LineData(name=name, id=id, type=transport))
        return ret
