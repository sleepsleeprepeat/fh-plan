from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Department(Enum):
    INFO_ELEKTRO = 1
    AGRAR = 2
    MASCHIENEN = 3
    WIRTSCHAFT = 4
    MEDIEN_BAU = 5
    SOZIAL_ARBEIT = 6


class EventType(Enum):
    VORLESUNG = 1
    UEBUNG = 2
    LABOR = 3


class Course(Enum):
    ELEKTROTECHNIK = 4
    INFORMATIK = 7
    MECHATRONIK = 11
    MEDIENINGINEUR = 12
    WIRTSCHAFTSINGIUER = 22


@dataclass
class Room:
    building: int
    floor: int
    room: int


@dataclass
class Lecturer:
    name: str
    email: str = None
    phone: str = None
    fax: str = None
    office: Room = None
    department: Department = None
    description: str = ""


@dataclass
class RawEvent:
    weeknums: list
    day: str
    year: int
    content: str
    start: str
    end: str
    course: Course
    semester: int
    group: str


@dataclass
class Event:
    title: str
    department: Department
    eventtype: EventType
    lecturer: Lecturer
    room: Room
    start: datetime
    end: datetime
    course: Course
    semester: int
    group: int


@dataclass
class StackedEvent:
    title: str
    department: Department
    eventtype: EventType
    lecturer: Lecturer
    room: Room
    dates: list[(datetime, datetime)]
    course: Course
    semesters: list[int]
    groups: list[int]
