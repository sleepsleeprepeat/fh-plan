from datetime import datetime
import re

from datatypes import (
    CATEGORY_EXERCISES,
    CATEGORY_LAB,
    SALUTATIONS,
    WEEKDAYS,
    Plan,
    Block,
    Event,
    Modul,
    RawEvent,
)

import pdfplumber


class BlockParser:
    def __init__(self, block: Block, timerange: list[str]):
        # lines are used to separate the title from the lecturers and rooms
        # as there is no way to filter the title by directly
        self.lines = block.content.split("\n")

        self.dates = self.__parse_dates(block, timerange)
        self.rooms = self.__parse_rooms()

        # this is to filter out the lecturers from the lines
        self.__parse_lecturers()

        self.title = self.__parse_title()
        self.category = self.__parse_category(self.title)

        self.events = []

    def __parse_dates(self, block, timerange) -> list[tuple[datetime, datetime]]:
        day_start = timerange[block.start]
        day_end = timerange[block.end]
        day_idx = WEEKDAYS.index(block.day)

        dates = []
        for weeknum in block.weeknums:
            start_str = f"{block.year} {weeknum} {day_idx} {day_start}"
            start = datetime.strptime(start_str, "%Y %W %w %H:%M")

            end_str = f"{block.year} {weeknum} {day_idx} {day_end}"
            end = datetime.strptime(end_str, "%Y %W %w %H:%M")

            dates.append((start, end))

        return dates

    def __parse_rooms(self) -> list:
        pattern = r"C\d\d-\d.\d\d"
        rooms = []
        for line in self.lines:
            res = re.findall(pattern, line)
            if not res:
                continue

            rooms.extend(res)
            self.lines.remove(line)

        return rooms

    def __parse_lecturers(self):
        for line in self.lines:
            if any(s in line for s in SALUTATIONS):
                self.lines.remove(line)

    def __parse_title(self) -> str:
        return " ".join(self.lines)

    def __parse_category(self, title) -> str:
        if any(match in title for match in CATEGORY_LAB):
            return "Labor"

        if any(match in title for match in CATEGORY_EXERCISES):
            return "Übung"

        return "Vorlesung"

    def parse(self) -> list[RawEvent]:
        for date in self.dates:
            event = RawEvent(
                self.title,
                self.rooms,
                self.category,
                date[0],
                date[1],
            )
            self.events.append(event)

        return self.events


class PageParser:
    def __init__(self, page):
        self.header = page.extract_text().split("\n")[:3]  # get the first 3 lines
        self.table = page.extract_table()

        self.weeknums = self.__parse_weeknums()
        self.timerange = self.__parse_timerange()
        self.year = self.__parse_year()

        self.blocks = []
        for row in self.table:
            self.blocks += self.__parse_row(row)

    def __parse_weeknums(self) -> list[int]:
        # the weeknums are in the 3rd line of the header
        # the text is formatted like this:
        # Kalenderwoche: 14, 20, 24 Datum: 4/4/22 bis 19/6/22
        txt = self.header[2][16:].split("Datum: ")[0].replace(" ", "")

        weeknums = []
        for t in txt.split(","):
            if "-" in t:
                start, end = t.split("-")
                start = int(start)
                end = int(end)
                weeknums.extend(list(range(start, end + 1)))
            else:
                weeknums.append(int(t))

        return weeknums

    def __parse_timerange(self) -> list[str]:
        # the timeheader of the table has the same text layered on top
        # of each other 3 times for some odd reason
        pattern = r"\d\d(\d)?\d?\d?(\d):(:):\d\d(\d)\d\d(\d)"

        times = []
        for time in self.table[0][1:-1]:
            res = list(re.match(pattern, time).groups())
            res = [x for x in res if x is not None]
            times.append("".join(res))

        return times

    def __parse_year(self) -> int:
        # the year is in the 2nd line of the header
        return int(self.header[1].split(" ")[1].split("/")[0])

    def __parse_row(self, row):
        day = row[0]  # get the day of the week from first cell
        row = row[1:-1]  # remove first cell (day) and last cell (always empty)

        blocks = []
        event = None
        tracking = False

        for idx, cell in enumerate(row):
            # if there is a non-empty cell start counting columns
            if isinstance(cell, str) and cell != "":
                tracking = True
                event = Block(
                    year=self.year,
                    weeknums=self.weeknums,
                    day=day,
                    start=idx,
                    end=0,
                    content=cell,
                )

            # if there is an empty cell stop count columns
            if tracking and cell == "":
                tracking = False
                event.end = idx
                blocks.append(event)

        return blocks

    def parse(self) -> list[RawEvent]:
        self.events = []
        for block in self.blocks:
            e = BlockParser(block, self.timerange).parse()
            self.events.extend(e)

        return self.events


class PlanParser:
    def __init__(self, path):
        self.pdf = pdfplumber.open(path)
        self.modules = []

        # Meta information about the plan
        self.title = ""
        self.semester = 0
        self.group = 0
        self.__parse_header()

        self.events = self.__parse_pages()

    def __parse_header(self):
        # get the first 3 lines of the first page
        header = self.pdf.pages[0].extract_text().split("\n")[:3]

        pattern = r"^Vorlesungsplan für\s+([\w\-\s]+) (\d+). Sem. Gruppe (\d+)"
        res = re.match(pattern, header[0])

        if not res:
            return

        self.title = res.group(1)
        self.semester = int(res.group(2))
        self.group = int(res.group(3))

    def __parse_pages(self):
        events = []
        for page in self.pdf.pages:
            events.extend(PageParser(page).parse())

        return events

    def parse(self) -> Plan:
        for e in self.events:
            # check if module with same title already exists
            modul = next((m for m in self.modules if m.title == e.title), None)

            if not modul:
                m = Modul(
                    title=e.title,
                    category=e.category,
                    events=[Event(e.start, e.end, e.rooms)],
                )
                self.modules.append(m)
            else:
                modul.events.append(Event(e.start, e.end, e.rooms))

        return Plan(
            title=self.title,
            semester=self.semester,
            group=self.group,
            modules=self.modules,
        )
