#!/usr/bin/env python3
"""Normalize the DOG 210 (30/10/2025) Galicia local-holiday resolution.

Annexes I-IV list numbered entries `N. Concello: date, feast; date, feast.`
with Spanish or Galician month spellings. The concello join uses the audited
normalized-name map (article reordering covers "Coruña, A" vs "A Coruña").
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, load_frozen, manifest_source,  # noqa: E402
                     parse_galician_date, parse_spanish_date, write_json)

SECTION_PROVINCE = {"A Coruña": "15", "Lugo": "27", "Ourense": "32",
                    "Pontevedra": "36"}

OMISSION_REASON = (
    "Sin par completo de fiestas locales en la resolución oficial del DOG 210 "
    "para 2026."
)


def parse_date(text: str) -> str | None:
    return parse_spanish_date(text) or parse_galician_date(text)


def main() -> None:
    source = manifest_source("dog-210-2025")
    html = load_frozen("dog-210-2025").decode("utf-8")
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    joiners = {prov: RosterJoiner(prov) for prov in SECTION_PROVINCE.values()}
    joiners["27"].add_alias("27", "Guntín de Pallares", "27023")
    joiners["32"].add_alias("32", "Rúa de Valdeorras", "32072")
    joiners["32"].add_alias("32", "Rúa de Valdeorras, A", "32072")
    municipalities: list[dict] = []
    section: str | None = None
    for line in lines:
        prov_match = re.fullmatch(r"Provincia: (.+)\.", line)
        if prov_match:
            section = prov_match.group(1)
            continue
        if section is None:
            continue
        entry = re.fullmatch(r"\d+\.\s*(.+?):\s*(.+)\s*", line)
        if entry is None:
            continue
        name = entry.group(1).strip()
        body = entry.group(2).strip()
        date_matches = re.findall(
            r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñç]+)", body.lower()
        )
        dates: list[str] = []
        for day, month in date_matches:
            parsed = parse_date(f"{day} de {month}")
            if parsed is not None and parsed not in dates:
                dates.append(parsed)
        if len(dates) != 2:
            raise RuntimeError(f"Galicia entry {name!r} has {len(dates)} dates")
        municipality = joiners[SECTION_PROVINCE[section]].join(
            SECTION_PROVINCE[section], name
        )
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Festa local",
                 "sourceRecordId": f"dog210:{name}:{d}"}
                for d in sorted(dates)
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Galicia codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "12"
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
        "autonomousCommunityCode": "12",
        "autonomousCommunity": "Galicia",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": "DOG 210 annexes I-IV; Spanish/Galician month spellings both accepted.",
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/galicia-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()