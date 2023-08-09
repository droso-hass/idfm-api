import aiohttp
import logging

LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"
STOP_AND_LINES = "https://data.iledefrance-mobilites.fr/explore/dataset/arrets-lignes/download/?format=json&timezone=Europe/Berlin&lang=fr"
STOP_RELATIONS = "https://data.iledefrance-mobilites.fr/explore/dataset/relations/download/?format=json&timezone=Europe/Berlin&lang=fr"
EXCHANGE_AREAS = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/zones-de-correspondance/exports/json?lang=fr&timezone=Europe/Berlin"

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Dataset:
    """
    Class used to generate the lines and stops listings

    The data is fetched only once per execution, the result is then cached as this process takes multiple seconds

    To find a list of all the stops we need to use multiple datasets:
    LINES
    -> get line ID
    -> STOP_AND_LINES -> get corresponding stops areas for trains (ZdAId) OR get corresponding stops points for other modes (ArRId)
    -> STOP_RELATIONS -> map the ArRid to ZdAId AND map the ZdAId to the exchange area (ZdCId)
    -> EXCHANGE_AREAS -> get the exchange area data

    So the process looks like this: LineID -> ZdAId -> ZdCId OR LineID -> ArId -> ZdAId -> ZdCId
    """

    lines = None
    stops = None

    @staticmethod
    async def get_lines(session: aiohttp.ClientSession) -> dict[str, list[dict]]:
        """
        Fetch the latest data from IDFM (if needed) and returns the available lines

        Args:
            session: aiohttp session
        Returns:
            dict[str,list[dict]]: a map of the TransportType to a list of lines (Name:ID)
        """
        if Dataset.lines is None:
            await Dataset.fetch_data(session)
        return Dataset.lines

    @staticmethod
    async def get_stops(session: aiohttp.ClientSession) -> dict[str, list[dict]]:
        """
        Fetch the latest data from IDFM (if needed) and returns the available stops

        Args:
            session: aiohttp session
        Returns:
            dict[str, list[dict]]: a map of the line id to a list of stops
        """
        if Dataset.stops is None:
            await Dataset.fetch_data(session)
        return Dataset.stops

    @staticmethod
    async def fetch_data(session: aiohttp.ClientSession):
        """
        Fetch and process the data from IDFM datasets

        Args:
            session: the aiohttp session
        """
        _LOGGER.debug("fetching idfm datasets")
        lines = {}
        line_ids = []
        for l in await (await session.get(LINES)).json():
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
        for i in await (await session.get(STOP_RELATIONS)).json():
            try:
                arid_to_zdaid[i["fields"]["arrid"]] = i["fields"]["zdaid"]
            except KeyError:
                pass
            try:
                zdaid_to_zdcid[i["fields"]["zdaid"]] = i["fields"]["zdcid"]
            except KeyError:
                pass

        zdc = {}
        for i in await (await session.get(EXCHANGE_AREAS)).json():
            zdc[i["zdcid"]] = i

        # map line to stops
        line_to_stops = {}
        stop_ids = {}
        for i in await (await session.get(STOP_AND_LINES)).json():
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
                    line_to_stops[id].append(
                        {
                            "exchange_area_id": None
                            if zdcid is None
                            else "STIF:StopArea:SP:" + zdcid + ":",
                            "exchange_area_name": None
                            if zdcid is None
                            else zdc[zdcid]["zdcname"],
                            "stop_id": "STIF:StopPoint:Q:" + stop_id + ":",
                            "name": i["fields"]["stop_name"],
                            "city": i["fields"]["nom_commune"],
                            "zipCode": i["fields"]["code_insee"],
                            "x": i["fields"]["stop_lat"],
                            "y": i["fields"]["stop_lon"],
                        }
                    )
                    stop_ids[id].append(stop_id)

        # remove lines with no associated stops
        filtered_lines = {}
        for mode, data in lines.items():
            for name, value in data.items():
                if value in line_to_stops:
                    if mode not in filtered_lines:
                        filtered_lines[mode] = {}
                    filtered_lines[mode][name] = value

        Dataset.lines = filtered_lines
        Dataset.stops = line_to_stops
