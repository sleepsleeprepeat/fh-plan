from dataclasses import dataclass
from datetime import datetime
import re

from datatypes import Course, EventType, Room, Lecturer, RawEvent, Event

import pdfplumber


class EventParser:
    def __init__(self, raw_event: RawEvent, timerange: list[str], pagetitle: str):
        self.timerange = timerange

        self.lines = raw_event.content.split("\n")
        self.weeknums = raw_event.weeknums
        self.start_column = raw_event.start
        self.end_column = raw_event.end
        self.day = raw_event.day
        self.year = raw_event.year
        self.weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        self.pagetitle = pagetitle  #! just for testing

        self.events = []

        self.rooms = self.parse_rooms()
        self.lecturers = self.parse_lecturers()
        self.title = self.parse_title()
        self.dates = self.parse_dates()
        self.eventtype = self.parse_eventtype()

    def parse_rooms(self) -> list[Room]:
        pattern = r"C(\d\d)-(\d).(\d\d)"

        rooms = []
        for line in self.lines:
            res = re.findall(pattern, line)
            if not res:
                continue

            for r in res:
                room = Room(int(r[0]), int(r[1]), int(r[2]))
                rooms.append(room)

            self.lines.remove(line)

        return rooms

    def parse_lecturers(self) -> list[Lecturer]:
        titles = ["Prof.", "Dr.", "Dipl.", "Hr.", "Fr."]

        lecturers = []
        for line in self.lines:
            if any(title in line for title in titles):
                lecturers.append(Lecturer(line))
                self.lines.remove(line)

        return lecturers

    def parse_title(self) -> str:
        return " ".join(self.lines)

    def parse_dates(self) -> datetime:
        start_time = self.timerange[self.start_column]
        end_time = self.timerange[self.end_column]
        day_num = self.weekdays.index(self.day)

        dates = []
        for weeknum in self.weeknums:
            start_str = f"{self.year} {weeknum} {day_num} {start_time}"
            start = datetime.strptime(start_str, "%Y %W %w %H:%M")

            end_str = f"{self.year} {weeknum} {day_num} {end_time}"
            end = datetime.strptime(end_str, "%Y %W %w %H:%M")

            dates.append((start, end))

        return dates

    def parse_eventtype(self) -> EventType:
        matches_exercise = ["-Ü", "Ü-"]
        matches_lab = ["-ÜL", "ÜL-"]

        if any(match in self.title for match in matches_lab):
            return EventType.LABOR

        if any(match in self.title for match in matches_exercise):
            return EventType.UEBUNG

        return EventType.VORLESUNG

    # TODO: add department
    def parse(self) -> list[Event]:
        for date in self.dates:
            event = Event(
                self.title,
                None,
                self.eventtype,
                self.lecturers,
                self.rooms,
                date[0],
                date[1],
                self.pagetitle,
            )
            self.events.append(event)

        return self.events


class PageParser:
    def __init__(self, page):
        self.header = page.extract_text().split("\n")[:3]  # get the first 3 lines
        self.table = page.extract_table()

        self.timerange = self.parse_timerange()
        self.weeknums = self.parse_weeknums()
        self.year = self.parse_year()
        self.pagetitle = self.parse_title()
        self.semester = self.parse_semester()
        self.course = self.parse_course()
        self.group = self.parse_group()

        print(self.semester)
        print(self.course)
        print(self.group)

        self.raw_events = []
        self.events = []

        self.parse_table()
        self.parse_events()

    def parse_title(self):
        return self.header[0].split("für")[1].lstrip()

    def parse_semester(self):
        pattern = r"^Vorlesungsplan für   (\d?\d). Sem. (.+)-Gruppe (\d?\d)"
        res = re.match(pattern, self.header[0])
        print(res)
        if res:
            return int(res.group(1))

    def parse_course(self):
        pattern = r"^Vorlesungsplan für   (\d?\d). Sem. (.+)-Gruppe (\d?\d)"
        res = re.match(pattern, self.header[0])
        if not res:
            return None

        if "Elektrotechnik" in res.group(2):
            return Course.ELEKTROTECHNIK
        elif "Informatik" in res.group(2) or "INF" in res.group(2):
            return Course.INFORMATIK
        elif "Mechatronik" in res.group(2):
            return Course.MECHATRONIK
        elif "Medieningenieur" in res.group(2):
            return Course.MEDIENINGENIEUR
        elif "Wirtschaftsingenieurwesen" in res.group(2) or "Wing" in res.group(2):
            return Course.WIRTSCHAFTSINGENIEURWESEN

    def parse_group(self):
        pattern = r"^Vorlesungsplan für   (\d?\d). Sem. (.+)-Gruppe (\d?\d)"
        res = re.match(pattern, self.header[0])
        if res:
            return int(res.group(3))

    def parse_year(self):
        return int(self.header[1].split(" ")[1].split("/")[0])

    def parse_weeknums(self) -> list[int]:
        txts = self.header[2][16:].split("Datum: ")[0].replace(" ", "").split(",")

        weeknums = []
        for txt in txts:
            if "-" in txt:
                start, end = txt.split("-")
                start = int(start)
                end = int(end)
                weeknums.extend(list(range(start, end + 1)))
            else:
                weeknums.append(int(txt))

        return weeknums

    def parse_timerange(self):
        # the timeheader of the table has the same text layered on top
        # of each other 3 times for some odd reason
        pattern = r"\d\d(\d)?\d?\d?(\d):(:):\d\d(\d)\d\d(\d)"

        times = []
        for time in self.table[0][1:-1]:
            res = list(re.match(pattern, time).groups())
            res = [x for x in res if x is not None]
            times.append("".join(res))

        return times

    def parse_events(self):
        for raw_event in self.raw_events:
            ep = EventParser(raw_event, self.timerange, self.pagetitle).parse()
            self.events.extend(ep)

    def parse_table(self):
        for row in self.table:
            self.parse_row(row)

    # this method finds all the events in a row
    def parse_row(self, row):
        day = row[0]  # get the day of the week from first cell
        row = row[1:-1]  # remove first cell (day) and last cell (always empty)

        tracked_event = None
        tracking_event = False

        for idx, cell in enumerate(row):
            # if there is a non-empty cell start counting columns
            if isinstance(cell, str) and cell != "":
                tracking_event = True
                tracked_event = RawEvent(self.weeknums, day, self.year, cell, idx, 0)

            # if there is an empty cell stop count columns
            if tracking_event and cell == "":
                tracking_event = False
                tracked_event.end = idx
                self.raw_events.append(tracked_event)


class DocumentParser:
    def __init__(self, path):
        self.path = path
        self.pdf = pdfplumber.open(path)
        self.pages = []
        self.events = []
        self.title = ""

    def parse(self) -> list[Event]:
        self.title = (
            self.pdf.pages[0].extract_text().split("\n")[0].split("für")[1].lstrip()
        )
        for idx, page in enumerate(self.pdf.pages):
            print(f"\033[94mPage: {idx+1}\033[0m")
            p = PageParser(page)
            p.parse_weeknums()
            p.parse_timerange()
            p.parse_table()
            self.pages.append(p)
            self.events += p.events
