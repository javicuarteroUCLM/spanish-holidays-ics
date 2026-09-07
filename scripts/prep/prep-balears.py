#!/usr/bin/env python3
"""Normalize the Dades Obertes Illes Balears 2026 work calendar.

The CSV lists municipal local days at localitat granularity (nuclei and
parròquies). The municipality-level pair is selected as: the localitat block
that matches the municipality name; otherwise the block containing the rows
with an empty Localitat field; otherwise the first block (capital locality).
Each selected block must contain exactly two rows.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, load_frozen, manifest_source,  # noqa: E402
                     normalized_name, parse_catalan_date, write_json)

ALIASES = {
    "Ciutadella": "07015",
    "Es Castell": "07064",
    "Es Mercadal": "07037",
    "Es Migjorn Gran": "07902",
    "Sa Pobla": "07044",
    "Ses Salines": "07059",
}

OMISSION_REASON = (
    "La fuente oficial de Dades Obertes Illes Balears no contiene un par de "
    "fiestas locales de ámbito municipal para este municipio en 2026."
)


def main() -> None:
    source = manifest_source("balears-calendari-laboral-2026")
    text = load_frozen("balears-calendari-laboral-2026").decode("latin-1")
    rows = list(csv.reader(text.splitlines()))
    if rows[0] != ["Illa", "Àmbit", "Municipi", "Localitat", "Data", "Nom festa"]:
        raise RuntimeError("Unexpected Balears CSV header")

    joiner = RosterJoiner("07")
    for name, code in ALIASES.items():
        joiner.add_alias("07", name, code)

    local = [r for r in rows[1:] if len(r) >= 6 and r[1].strip() == "Local"]
    by_mun: dict[str, list[list[str]]] = defaultdict(list)
    for r in local:
        by_mun[r[2].strip()].append(r)

    municipalities: list[dict] = []
    for source_name, entries in sorted(by_mun.items()):
        municipality = joiner.join("07", source_name)
        blocks: dict[str, list[list[str]]] = defaultdict(list)
        for r in entries:
            blocks[r[3].strip()].append(r)
        empty = blocks.get("", [])
        exact = [b for b in blocks if b and normalized_name(b) == normalized_name(source_name)]
        if exact:
            chosen = exact[0]
        elif empty:
            empty_dates = {parse_catalan_date(r[4]) for r in empty}
            candidates = [
                b for b, rs in blocks.items()
                if b and {parse_catalan_date(r[4]) for r in rs} >= empty_dates
            ]
            if len(candidates) != 1:
                raise RuntimeError(f"Ambiguous empty-row block for {source_name}")
            chosen = candidates[0]
        else:
            non_empty = [b for b in blocks if b]
            chosen = sorted(non_empty)[0] if non_empty else None
        block = blocks[chosen]
        if len(block) != 2:
            raise RuntimeError(f"Block {source_name}/{chosen} has {len(block)} rows")
        holidays = []
        for r in block:
            date = parse_catalan_date(r[4])
            if date is None:
                raise RuntimeError(f"Bad Balears date {r[4]!r} for {source_name}")
            holidays.append({
                "date": date,
                "name": r[5].strip(),
                "sourceRecordId": f"{source_name}:{r[4].strip()}",
            })
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "manual-alias" if source_name in ALIASES else "normalized-name",
            "sourceName": source_name,
            "localitat": chosen,
            "holidays": holidays,
        })

    municipalities.sort(key=lambda m: m["ineCode"])
    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "04"
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
        "autonomousCommunityCode": "04",
        "autonomousCommunity": "Illes Balears",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            "Municipality-level pair selected per localitat block rules; "
            "nuclear/parròquia rows are not merged into the municipality pair."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/illes-balears-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()