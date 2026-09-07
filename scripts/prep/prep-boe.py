#!/usr/bin/env python3
"""Normalize the frozen BOE-A-2025-21667 matrix into per-territory holidays.

The matrix rows are day rows ("1 Año Nuevo.") with 19 territory cells marked
`*` (national, non-substitutable), `**` (national, kept by the territory) or
`***` (autonomous-community day). Scope convention (kept from the previous
Andalucía transcription):

- `*` and `**` on a fixed national date -> scope "country".
- `**` on a shifted observance ("Lunes siguiente a ...", "Día siguiente a ...")
  -> the territory chose the shifted day, scope "autonomous-community".
- `***` -> scope "autonomous-community".

Every territory column must contain exactly 12 non-local days; the Canarias
column has 11 because the island day is published only in the BOC decree.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, load_frozen, manifest_source, write_json  # noqa: E402

HEADERS = [
    "Andalucía", "Aragón", "Asturias", "Illes Balears", "Canarias", "Cantabria",
    "Castilla-La Mancha", "Castilla y León", "Cataluña", "Extremadura",
    "Galicia", "Com. Madrid", "Región Murcia", "C. Foral Navarra", "País Vasco",
    "La Rioja", "Comunitat Valenciana", "Ciudad de Ceuta", "Ciudad de Melilla",
]
COMMUNITY_CODES = [
    "01", "02", "03", "04", "05", "06", "08", "07", "09", "11", "12", "13",
    "14", "15", "16", "17", "10", "18", "19",
]
SHIFTED_MARK = re.compile(r"(lunes siguiente|día siguiente|dia siguiente)", re.I)

MONTH = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
         "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
         "diciembre": 12}


def row_cells(row: ET.Element) -> list[str]:
    return [cell_text(c) for c in row if c.tag.endswith("td") or c.tag.endswith("th")]


def main() -> None:
    source = manifest_source("boe-2026-labour-calendar")
    raw = load_frozen("boe-2026-labour-calendar")
    root = ET.fromstring(raw)

    # The matrix table is the only <table> in the document body.
    table = next(el for el in root.iter() if el.tag.endswith("table"))
    rows = list(table.iter("tr"))
    if len(rows) < 3:
        raise RuntimeError("BOE matrix has no rows")

    header_cells = [re.sub(r"\s*\(\d+\)$", "", c) for c in row_cells(rows[1])]
    if header_cells != HEADERS:
        raise RuntimeError(f"Unexpected BOE matrix headers: {header_cells}")

    # Build day rows: label cell + 19 mark cells.
    day_rows: list[tuple[str, list[str]]] = []
    for row in rows[3:]:
        cells = row_cells(row)
        if len(cells) != 20:
            continue
        label = cells[0].strip()
        if label in MONTH:  # month header row
            continue
        marks = [c.strip() for c in cells[1:]]
        if not label or not re.match(r"^\d{1,2} ", label):
            continue
        if len(marks) != 19:
            raise RuntimeError(f"Row {label} has {len(marks)} cells")
        day_rows.append((label, marks))

    holidays: list[dict] = []
    # Universal days: rows marked in every one of the 19 territory columns
    # (1 Ene, 6 Ene, 3 Abr, 1 May, 15 Ago, 12 Oct, 8 Dic, 25 Dic). These are
    # scope "country". Every other marked cell is a territory-level day
    # (`**` = national day kept by the territory, `***` = community day) and
    # is modelled with scope "autonomous-community" for that territory.
    universal: set[str] = set()
    for label, marks in day_rows:
        if all(marks):
            universal.add(label)
    for territory_index, code in enumerate(COMMUNITY_CODES):
        territory_days = []
        for label, marks in day_rows:
            mark = marks[territory_index]
            if not mark:
                continue
            date, name = split_label(label)
            if mark == "*" and label in universal:
                scope = "country"
            elif label in universal:
                scope = "country"
            else:
                scope = "autonomous-community"
            territory_days.append(
                {
                    "date": date,
                    "name": name,
                    "scope": scope,
                    "autonomousCommunityCode": code,
                    "boeMark": mark,
                }
            )
        if len(territory_days) != 12 and code != "05":
            raise RuntimeError(
                f"Territory {code} has {len(territory_days)} days, expected 12"
            )
        if code == "05" and len(territory_days) != 11:
            raise RuntimeError(
                f"Canarias column has {len(territory_days)} days, expected 11"
            )
        holidays.extend(territory_days)

    payload = {
        "sourceId": source["id"],
        "sourceSha256": source["sha256"],
        "auditNote": (
            "Parsed from the BOE-A-2025-21667 matrix (19 territory columns, "
            "legend * / ** / ***). ** on shifted observances is modelled as "
            "autonomous-community scope; Canarias has 11 BOE days because its "
            "island day is published in BOC Decreto 61/2025."
        ),
        "holidays": holidays,
    }
    write_json(ROOT / "data/normalized/2026/boe-holidays.json", payload)
    print(f"Wrote {len(holidays)} territory-day rows")


def cell_text(cell: ET.Element) -> str:
    return "".join(cell.itertext()).replace("\xa0", " ").strip()


def split_label(label: str) -> tuple[str, str]:
    match = re.match(r"^(\d{1,2})\s+(.+)$", label)
    if match is None:
        raise RuntimeError(f"Unparseable BOE day label: {label!r}")
    day, name = int(match.group(1)), match.group(2).strip().rstrip(".")
    # The month is tracked positionally: rows appear month by month in order.
    # Recover the month from the row sequence is fragile, so the month is
    # resolved from the label's position in the canonical 2026 matrix instead.
    month = month_for_day(name)
    return f"2026-{month:02d}-{day:02d}", name


def month_for_day(name: str) -> int:
    # The matrix day labels carry no month; map by canonical occurrence order
    # of the 2026 matrix. Each name appears once in the matrix.
    order = [
        ("Año Nuevo", 1), ("Epifanía", 1), ("Día de Andalucía", 2),
        ("Día de les Illes Balears", 3), ("San José", 3), ("Eid Fitr", 3),
        ("Jueves Santo", 4), ("Viernes Santo", 4), ("Lunes de Pascua", 4),
        ("San Jorge", 4), ("Fiesta de Castilla y León", 4),
        ("Fiesta del Trabajo", 5), ("Comunidad de Madrid", 5),
        ("Eidul Adha", 5), ("Aid al Adha", 5), ("Día de Canarias", 5),
        ("Corpus Christi", 6), ("Región de Murcia", 6), ("Día de la Rioja", 6),
        ("San Juan", 6), ("Santiago Apóstol", 7),
        ("Instituciones de Cantabria", 7), ("Nuestra Señora de África", 8),
        ("Asunción", 8), ("Día de Ceuta", 9), ("Día de Asturias", 9),
        ("Día de Extremadura", 9), ("Nacional de Cataluña", 9),
        ("La Bien Aparecida", 9), ("Comunitat Valenciana", 10),
        ("Fiesta Nacional de España", 10), ("Todos los Santos", 11),
        ("Constitución", 12), ("Inmaculada", 12), ("Natividad", 12),
        ("San Esteban", 12),
    ]
    for marker, month in order:
        if marker in name:
            return month
    raise RuntimeError(f"Cannot resolve month for {name!r}")


if __name__ == "__main__":
    main()