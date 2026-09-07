#!/usr/bin/env python3
"""Normalize the BORM 163 (17/07/2025) Murcia local-holiday table.

The annex is a numbered 45-row table `N NAME weekday day Month weekday day
Month`. Names are uppercase; two rows carry a trailing period.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, parse_spanish_date, write_json)

MONTHS = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
          "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11,
          "DICIEMBRE": 12}
WEEKDAYS = r"(LUNES|MARTES|MIÉRCOLES|MIERCOLES|JUEVES|VIERNES|SÁBADO|SABADO|DOMINGO)"

OMISSION_REASON = (
    "El municipio no figura en la relación oficial de fiestas locales de 2026 "
    "del BORM 163."
)


def main() -> None:
    source = manifest_source("borm-163-2025")
    text = extract_pdf("borm-163-2025")
    load_frozen("borm-163-2025")

    rows = []
    for line in text.splitlines():
        line = line.strip()
        match = re.fullmatch(
            rf"(\d{{1,2}}) (.+?) {WEEKDAYS} (\d{{1,2}}) ([A-Za-zÑñ]+) {WEEKDAYS} (\d{{1,2}}) ([A-Za-zÑñ]+)",
            line,
            flags=re.IGNORECASE,
        )
        if match is None:
            continue
        name = re.sub(r"\.$", "", match.group(2)).strip()
        d1 = parse_spanish_date(f"{match.group(4)} de {match.group(5).lower()}")
        d2 = parse_spanish_date(f"{match.group(7)} de {match.group(8).lower()}")
        if d1 is None or d2 is None:
            raise RuntimeError(f"Bad Murcia dates in row {line!r}")
        rows.append((int(match.group(1)), name, d1, d2))
    if len(rows) != 45:
        raise RuntimeError(f"Expected 45 Murcia rows, found {len(rows)}")

    joiner = RosterJoiner("30")
    joiner.add_alias("30", "FUENTE ÁLAMO", "30021")
    municipalities = []
    for number, name, d1, d2 in rows:
        municipality = joiner.join("30", name)
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": name,
            "sourceRow": number,
            "holidays": [
                {"date": d1, "name": "Fiesta local", "sourceRecordId": f"row:{number}:1"},
                {"date": d2, "name": "Fiesta local", "sourceRecordId": f"row:{number}:2"},
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "14"
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
        "autonomousCommunityCode": "14",
        "autonomousCommunity": "Región de Murcia",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": "Numbered 45-row table from BORM 163; name join via normalized names.",
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/region-de-murcia-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()