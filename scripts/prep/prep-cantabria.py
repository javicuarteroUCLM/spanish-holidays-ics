#!/usr/bin/env python3
"""Normalize the BOC 238 (11/12/2025) Cantabria local-holiday table.

The annex table `AYUNTAMIENTO | FESTIVIDAD | DÍA | MES` extracts as blocks of
text lines; the municipality name is recovered as the longest roster prefix of
the first text line (some rows merge name and first feast on one line).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, normalized_name, write_json)

MONTHS = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
          "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11,
          "DICIEMBRE": 12}
CHROME = ("boletín", "boc.cantabria", "jueves,", "cve-", "ayuntamiento festividad",
          "pág.", "=== ", "núm.", "2025/10276")
ALIASES = {
    "ARENAS IGUÑA": "39004",
    "CASTRO URDIALES": "39020",
    "HDAD. CAMPOO DE SUSO": "39032",
    "TRESVISO, LA VILLA DE": "39088",
    "ROZAS DE VALDEARROYO": "39065",
}
OMISSION_REASON = (
    "Sin par de fiestas locales en la resolución oficial del BOC 238 para 2026."
)


def main() -> None:
    source = manifest_source("boc-238-2025")
    text = extract_pdf("boc-238-2025")
    load_frozen("boc-238-2025")

    lines = []
    started = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if not started and line.upper() != "FIESTAS LOCALES":
            continue
        started = True
        if line.lower().startswith(CHROME) or line.upper() == "FIESTAS LOCALES":
            continue
        lines.append(line)

    # State machine: text lines accumulate; numeric lines are days; month
    # lines close the block when the second month arrives.
    joiner = RosterJoiner("39")
    for name, code in ALIASES.items():
        joiner.add_alias("39", name, code)
    roster_names = {normalized_name(m["name"]): m["ineCode"] for m in joiner.roster}

    blocks: list[dict] = []
    texts: list[str] = []
    days: list[str] = []
    months: list[str] = []
    for line in lines:
        if line in MONTHS:
            months.append(line)
            if len(months) == 2:
                if len(days) != 2:
                    raise RuntimeError(f"Block has {len(days)} days: {texts}")
                blocks.append({"texts": texts, "days": days, "months": months})
                texts, days, months = [], [], []
            continue
        if re.fullmatch(r"\d{1,2}", line):
            days.append(line)
            continue
        texts.append(line)
    if texts or days or months:
        raise RuntimeError(f"Dangling Cantabria block: {texts} {days} {months}")

    municipalities: list[dict] = []
    for block in blocks:
        first = block["texts"][0]
        # Longest prefix of the first line matching the roster.
        name = None
        words = first.split(" ")
        for size in range(len(words), 0, -1):
            candidate = " ".join(words[:size])
            try:
                municipality = joiner.join("39", candidate)
                name = candidate
                break
            except RuntimeError:
                continue
        if name is None:
            # Whole first line may be an alias-only name.
            municipality = joiner.join("39", first)
        d1 = f"2026-{MONTHS[block['months'][0]]:02d}-{int(block['days'][0]):02d}"
        d2 = f"2026-{MONTHS[block['months'][1]]:02d}-{int(block['days'][1]):02d}"
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "manual-alias" if name in ALIASES else "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d1, "name": "Fiesta local", "sourceRecordId": f"boc238:{name}:{d1}"},
                {"date": d2, "name": "Fiesta local", "sourceRecordId": f"boc238:{name}:{d2}"},
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Cantabria codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "06"
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
        "autonomousCommunityCode": "06",
        "autonomousCommunity": "Cantabria",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            "Longest-roster-prefix name recovery; abbreviated gazette names "
            "resolved by explicit aliases."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/cantabria-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()