from dataclasses import dataclass
from datetime import datetime

# --- Constants ---
WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
SALUTATIONS = ["Prof.", "Dr.", "Dipl.", "Hr.", "Fr."]
CATEGORY_EXERCISES = ["-Ü", "Ü-"]
CATEGORY_LAB = ["-ÜL", "ÜL-"]


# --- Data ---


@dataclass
class Plan:
    title: str
    semester: int
    group: int
    modules: list


@dataclass
class Modul:
    title: str
    category: str
    events: list


@dataclass
class Event:
    start: datetime
    end: datetime
    rooms: list


# --- Raw Data ---


@dataclass
class Block:
    year: int
    weeknums: list
    day: str
    start: str
    end: str
    content: str


@dataclass
class RawEvent:
    title: str
    rooms: list
    category: str
    start: datetime
    end: datetime
