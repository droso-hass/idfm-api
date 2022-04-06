from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from functools import total_ordering
from enum import Enum, IntEnum, unique
from idfm_api.utils import strip_html

@unique
class InfoSeverity(IntEnum):
    """
    Represents the serverity of an event
    """
    INFO = 0 # informative message
    WARNING = 1 # non blocking perturbation
    ERROR = 2 # blocking perturbation (usually planned)
    CRICTICAL = 3 # blocking perturbation (max level)

@unique
class TransportType(str, Enum):
    """
    Represents the type of transport
    """
    METRO = "metro"
    TRAM = "tramway"
    TRAIN = "train"
    BUS = "bus"

@dataclass(frozen=True)
class LineData:
    """
    Represents a line of a transport
    """
    name: str
    id: str
    type: TransportType

@dataclass(frozen=True)
class StopData:
    """
    Represents a stop area of a line
    """
    name: str
    id: str
    x: float
    y: float
    zip_code: str
    city: str

    @staticmethod
    def from_json(data: dict):
        return StopData(name=data.get("name"), id=data.get("id"), x=data.get("x"), y=data.get("y"), zip_code=data.get("zipCode"), city=data.get("city"))

@dataclass(frozen=True)
class InfoData:
    """
    Represents a traffic information fragment
    """
    id: str
    name: str
    message: str
    start_time: datetime
    end_time: datetime
    severity: InfoSeverity
    type: int

    @staticmethod
    def from_json(data: dict):
        return InfoData(name=data.get("title"), id=data.get("id"), message=strip_html(data.get("message")), start_time=datetime.strptime(data.get("impactStartTime"), '%Y-%m-%dT%H:%M'), end_time=datetime.strptime(data.get("impactEndTime"), '%Y-%m-%dT%H:%M'), type=data.get("type"), severity=InfoSeverity(data.get("severity")))

@dataclass(frozen=True)
@total_ordering
class TrafficData:
    """
    Represents a schedule for a specific path
    """
    line_id: str
    short_name: str
    direction: str
    forward: bool
    schedule: Optional[datetime]

    @staticmethod
    def from_json(data: dict):
        schedule_dt = None
        code = data.get("code")
        if code == "message":
            if data.get("schedule") == "A quai":
                schedule_dt = datetime.now()
        elif code == "duration":
            schedule_dt = datetime.now() + timedelta(minutes = int(data.get("time")))
        
        return TrafficData(line_id=data.get("lineId"), short_name=data.get("shortName"), direction=data.get("lineDirection"), forward=data.get("sens") == "1", schedule=schedule_dt)

    def __eq__(self, other):
        if type(other) is TrafficData:
            return self.schedule == other.schedule and self.line_id == other.line_id and self.direction == other.direction
        else:
            return False

    def __lt__(self, other):
        if type(other) is datetime:
            return self.schedule < other
        elif type(other) is TrafficData:
            return ((self.schedule is None or other.schedule is None) or self.schedule < other.schedule) or self.direction < other.direction
        else:
            return NotImplemented
    