#!/usr/bin/env python3
"""Normalize the BOPA 114 (16/06/2025) Asturias local-holiday resolution.

Annex: concejo name followed by date lines. Some concejos list parroquia-level
variants; the municipality pair is the first two concejo-wide entries (lines
whose qualifier is "en todo el municipio/Concejo" or carry no locality
qualifier). Concejos with fewer than two concejo-wide entries are omitted.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, parse_spanish_date, write_json)

SKIP_PREFIXES = ("https://", "BOLETÍN", "núm.", "Cód.", "en oviedo,", "===")
OMISSION_REASON = (
    "La resolución oficial del BOPA no contiene dos fiestas locales de ámbito "
    "de concejo para 2026: las fechas publicadas son específicas de parroquia "
    "o núcleos, o la fiesta patronal es movible sin fecha fija."
)


MONTH_RE = (
    r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    r"octubre|noviembre|diciembre)"
)


def main() -> None:
    source = manifest_source("bopa-114-2025")
    text = extract_pdf("bopa-114-2025")
    load_frozen("bopa-114-2025")

    entries: list[tuple[str, list[tuple[str, str]]]] = []
    pending_name = ""
    lines = text.splitlines()
    annex_start = next(
        (i for i, line in enumerate(lines) if "las siguientes:" in line),
        None,
    )
    if annex_start is None:
        raise RuntimeError("BOPA annex start not found")
    for line in lines[annex_start + 1:]:
        line = line.strip()
        if not line or line.startswith(SKIP_PREFIXES):
            continue
        if re.match(r"^\d{1,2}\s", line):
            # date-only continuation line: attach to the pending concejo
            date_match = re.match(rf"(\d{{1,2}})\s+(?:de\s+)?{MONTH_RE}", line)
            if date_match is None:
                raise RuntimeError(f"Bad BOPA date line: {line!r}")
            date = parse_spanish_date(
                f"{date_match.group(1)} de {date_match.group(2)}"
            )
            qualifier = line[date_match.end():].strip()
            if pending_name:
                entries.append((pending_name, [(date, qualifier)]))
                pending_name = ""
            else:
                if not entries:
                    raise RuntimeError(f"Date line before any concejo: {line!r}")
                name, dates = entries[-1]
                entries[-1] = (name, [*dates, (date, qualifier)])
            continue
        date_match = re.search(
            rf"(\d{{1,2}})\s+(?:de\s+)?{MONTH_RE}", line
        )
        if date_match is None:
            # Standalone concejo name (possibly wrapped) or chrome.
            if (
                len(line) <= 60
                and not line.endswith(",")
                and "/" not in line
                and "parroquia" not in line.lower()
            ):
                pending_name = line
            continue
        date = parse_spanish_date(f"{date_match.group(1)} de {date_match.group(2)}")
        if date is None:
            raise RuntimeError(f"Bad BOPA date in {line!r}")
        name_part = line[: date_match.start()].strip()
        qualifier = line[date_match.end():].strip()
        full_name = f"{pending_name} {name_part}".strip() if pending_name else name_part
        pending_name = ""
        entries.append((full_name, [(date, qualifier)]))

    # Merge wrapped concejo names ("muros de" + "nalÓn ...").
    merged_entries: list[tuple[str, list[tuple[str, str]]]] = []
    for name, dated in entries:
        if (
            merged_entries
            and len(merged_entries[-1][1]) == 1
            and name[:1].islower()
            and merged_entries[-1][0][-1:].islower()
        ):
            prev_name, prev_dates = merged_entries[-1]
            merged_entries[-1] = (f"{prev_name} {name}", [*prev_dates, *dated])
        else:
            merged_entries.append((name, dated))

    joiner = RosterJoiner("33")
    municipalities: list[dict] = []
    incomplete: list[str] = []
    for name, dated_entries in merged_entries:
        concejo_wide = [
            (date, qualifier) for date, qualifier in dated_entries
            if "todo el" in qualifier.lower()
            or "resto del" in qualifier.lower()
            or re.search(r"\ben\b", qualifier.lower()) is None
        ]
        if len(concejo_wide) < 2:
            incomplete.append(name)
            continue
        municipality = joiner.join("33", name)
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": date, "name": qualifier or "Fiesta local",
                 "sourceRecordId": f"bopa114:{name}:{date}"}
                for date, qualifier in concejo_wide[:2]
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Asturias codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "03"
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
        "autonomousCommunityCode": "03",
        "autonomousCommunity": "Asturias",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            "Concejo-wide pairs selected from the first two entries without a "
            "parroquia/nucleus qualifier; parroquia-level variants are not "
            f"merged. Concejos without a pair: {', '.join(incomplete)}."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/asturias-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()