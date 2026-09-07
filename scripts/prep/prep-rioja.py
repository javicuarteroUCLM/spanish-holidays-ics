#!/usr/bin/env python3
"""Normalize the BOR 159 (19/08/2025) La Rioja local-holiday resolution.

Annex lines are `Localidad: day y day (feast)`. Pedanía entries (12 in 2026)
do not create calendars; a municipality's calendar uses its own entry only.
Municipalities with a single date (Pinillos, Rabanera) are omitted. The final
clause "Restantes municipios... las dos fiestas tradicionales" does not name
dates and therefore cannot produce evidence for the 11 absent municipalities.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, parse_spanish_date, write_json)

MONTHS_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
             "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
             "noviembre": 11, "diciembre": 12}


def extract_dates(rest: str) -> list[str]:
    """Return the distinct ISO dates in a La Rioja entry tail."""
    parts = re.split(r"\s+y\s+", rest)
    dates: list[str] = []
    pending_days: list[int] = []
    for part in parts:
        days = [int(d) for d in re.findall(r"\d{1,2}", part)]
        months = [m for m in re.findall(r"[a-záéíóúñ]+", part.lower())
                  if m in MONTHS_ES]
        while pending_days and months:
            dates.append(f"2026-{MONTHS_ES[months[0]]:02d}-{pending_days.pop(0):02d}")
        if len(days) > len(months):
            pending_days.extend(days[: len(days) - len(months)])
            days = days[len(days) - len(months):]
        for day, month in zip(days, months):
            dates.append(f"2026-{MONTHS_ES[month]:02d}-{day:02d}")
    return sorted(set(dates))


OMISSION_REASON = (
    "Ausente de la resolución oficial de fiestas locales de 2026 del BOR 159 "
    "o con una sola fecha; la cláusula de «fiestas tradicionales» no fija "
    "fechas concretas."
)


def main() -> None:
    source = manifest_source("bor-159-2025")
    text = extract_pdf("bor-159-2025").replace("\uffff", " ")
    load_frozen("bor-159-2025")

    entries: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        line = line.strip()
        if ":" not in line or "Restantes municipios" in line:
            continue
        name, rest = line.split(":", 1)
        name = name.strip()
        dates = extract_dates(rest)
        if dates:
            entries.append((name, dates))
    if len(entries) < 160:
        raise RuntimeError(f"Too few La Rioja entries: {len(entries)}")

    joiner = RosterJoiner("26")
    joiner.add_alias("26", "Pradillo de Cameros", "26118")
    municipalities: list[dict] = []
    single_date: list[str] = []
    pedanias: list[str] = []
    for name, dates in entries:
        if len(dates) != 2:
            single_date.append(name)
            continue
        try:
            municipality = joiner.join("26", name)
        except RuntimeError:
            pedanias.append(name)
            continue
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Fiesta local", "sourceRecordId": f"bor159:{name}:{d}"}
                for d in dates
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate La Rioja codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "17"
    }
    covered = {m["ineCode"] for m in municipalities}
    if not covered <= set(roster):
        raise RuntimeError(f"Unknown codes: {covered - set(roster)}")
    omissions = [
        {"ineCode": code, "name": roster[code]["name"], "reason": OMISSION_REASON}
        for code in sorted(set(roster) - covered)
    ]

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "17",
        "autonomousCommunity": "La Rioja",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            f"Pedanía rows not merged ({len(pedanias)}): "
            f"{', '.join(sorted(pedanias))}. Single-date rows: "
            f"{', '.join(sorted(single_date))}."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/la-rioja-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()