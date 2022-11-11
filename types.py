from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Fachbereich(Enum):
    INFO_ELEKTRO = 1
    AGRAR = 2
    MASCHIENEN = 3
    WIRTSCHAFT = 4
    MEDIEN_BAU = 5
    SOZIAL_ARBEIT = 6


class Veranstaltungsart(Enum):
    VORLESUNG = 1
    UEBUNG = 2
    SEMINAR = 3
    LABOR = 4
    PROJEKT = 5
    SONSTIGE = 6


class Raum:
    gebaeude: int
    stockwerk: int
    raumnummer: int

    def __init__(self, gebaeude, stockwerk, raumnummer):
        self.gebaeude = gebaeude
        self.stockwerk = stockwerk
        self.raumnummer = raumnummer

    def __str__(self):
        return f"C{self.gebaeude}-{self.stockwerk}.{self.raumnummer}"


@dataclass
class Dozent:
    name: str
    email: str
    telefon: str
    fax: str
    buero: Raum
    fachbereich: Fachbereich
    beschreibung: str


class Event:
    titel: str
    fachbereich: Fachbereich
    Veranstaltungsart: Veranstaltungsart
    dozent: Dozent
    raum: Raum
    beginn: datetime
    ende: datetime
