from fhparser import PlanParser
import json


def main():
    file = "./input/WS_22_23/1.sem_e-technik-4.pdf"

    plan = PlanParser(file).parse()

    print(f"Studiengang: {plan.title}")
    print(f"Semester:    {plan.semester}")
    print(f"Gruppe:      {plan.group}")

    json_str = {
        "title": plan.title,
        "semester": plan.semester,
        "group": plan.group,
        "modules": [],
    }

    for m in plan.modules:
        json_str["modules"].append(
            {
                "title": m.title,
                "category": m.category,
                "events": [
                    {
                        "start": e.start.isoformat(),
                        "end": e.end.isoformat(),
                        "rooms": e.rooms,
                    }
                    for e in m.events
                ],
            }
        )

    with open("output.json", "w") as f:
        json.dump(json_str, f, indent=4)


if __name__ == "__main__":
    main()
