import json
import os
from datatypes import StackedEvent
from parser import DocumentParser


def read_pdf_folder(folder_name):
    directory = os.fsencode(folder_name)
    file_list = []
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".pdf"):
            file_list.append(filename)
    return file_list


def main():
    file_list = read_pdf_folder("input")

    single_file = "1.sem_e-technik-3.pdf"

    events = []
    if not single_file:
        for file in file_list:
            print(f"\033[92m{file}\033[0m")
            dp = DocumentParser(f"input/{file}")
            dp.parse()
            events += dp.events
    else:
        print(f"\033[92m{single_file}\033[0m")
        dp = DocumentParser(f"input/{single_file}")
        dp.parse()
        events += dp.events

    print("\n-----------------------------------------")
    print(f"\033[98m{len(events)} events parsed\033[0m")

    # compact events with same title, department, eventtype, lecturer, room and make a list with start and end dates
    compacted_events = []
    for event in events:
        for c_event in compacted_events:
            if (
                event.title == c_event.title
                and event.department == c_event.department
                and event.eventtype == c_event.eventtype
                and event.lecturer == c_event.lecturer
                and event.room == c_event.room
            ):
                c_event.dates.append((event.start, event.end))
                break
        else:
            compacted_events.append(
                StackedEvent(
                    event.title,
                    event.department,
                    event.eventtype,
                    event.lecturer,
                    event.room,
                    [(event.start, event.end)],
                    event.extra,
                )
            )

    print(f"\033[98m{len(compacted_events)} events compacted\033[0m")

    # print events
    for event in compacted_events:
        print(event.title)
        print("----------------")


if __name__ == "__main__":
    main()
