#!/usr/bin/env python3
"""Normalize the Comunidad de Madrid 2026 local-holiday chain.

Base resolution BOCM-20251212-34 (2 Dec 2025), amendment BOCM-20251229-19
(15 Dec 2025) and amendment BOCM-20260108-18 (22 Dec 2025). The PDF text has
inter-letter spacing artifacts on justified lines; parsing de-spaces each line
before extracting `Name: d1 y d2 de month` (or `d1 de m1 y d2 de m2`).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, parse_spanish_date, write_json)

MONTH_NAMES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|"
    "octubre|noviembre|diciembre"
)
DATE_PATTERNS = [
    re.compile(rf"^(\d{{1,2}})y(\d{{1,2}})de({MONTH_NAMES})$"),
    re.compile(rf"^(\d{{1,2}})de({MONTH_NAMES})y(\d{{1,2}})(?:de)?({MONTH_NAMES})$"),
]
ENTITY_NAMES = {"Cerceda", "Mataelpino", "El Espartal"}

OMISSION_REASON = (
    "Sin registro oficial de fiestas locales de 2026: el municipio figura como "
    "\u00abno comunicado\u00bb o sin par completo tras la cadena de resoluciones "
    "del BOCM (base 12/12/2025 y modificaciones)."
)

ALIASES = {
    "Berzosa de Lozoya": "28020",
    "Buitrago de Lozoya": "28027",
    "Braojos de la Sierra": "28024",
    "Valdetorres del Jarama": "28164",
}


def parse_entries(text: str) -> dict[str, list[str]]:
    """Return {name: [iso dates]} from a Madrid annex text."""
    entries: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if "—" not in line:
            continue
        line = line.replace("—", "", 1).strip()
        compact = re.sub(r"\s+", "", line)
        compact = compact.rstrip(".")
        if "nocomunicado" in compact.lower():
            continue
        if ":" in compact:
            name, rest = compact.split(":", 1)
        else:
            match = re.match(r"^([^\d]+)(\d.*)$", compact)
            if match is None:
                continue
            name, rest = match.group(1), match.group(2)
        if not rest:
            continue
        rest = re.sub(r"\([^)]*\)", "", rest)
        dates: list[str] | None = None
        for pattern in DATE_PATTERNS:
            match = pattern.fullmatch(rest)
            if match is None:
                continue
            groups = match.groups()
            if len(groups) == 4:
                d1 = parse_spanish_date(f"{groups[0]} de {groups[1]}")
                d2 = parse_spanish_date(f"{groups[2]} de {groups[3]}")
            else:
                d1 = parse_spanish_date(f"{groups[0]} de {groups[2]}")
                d2 = parse_spanish_date(f"{groups[1]} de {groups[2]}")
            if d1 is None or d2 is None:
                raise RuntimeError(f"Bad Madrid dates in {compact!r}")
            dates = [d1, d2]
            break
        if dates is None:
            entries[name] = []  # locality-specific entries without a single pair
            continue
        if name in entries:
            raise RuntimeError(f"Duplicate Madrid entry: {name}")
        entries[name] = dates
    return entries


def main() -> None:
    base = parse_entries(extract_pdf("bocm-20251212-34"))
    amend1 = parse_entries(extract_pdf("bocm-20251229-19"))
    amend2 = parse_entries(extract_pdf("bocm-20260108-18"))
    for sid in ("bocm-20251212-34", "bocm-20251229-19", "bocm-20260108-18"):
        load_frozen(sid)

    merged = dict(base)
    for name, dates in amend1.items():
        merged[name] = dates
    for name, dates in amend2.items():
        merged[name] = dates

    joiner = RosterJoiner("28")
    for name, code in ALIASES.items():
        joiner.add_alias("28", name, code)

    municipalities: list[dict] = []
    entity_rows: list[str] = []
    locality_specific: list[str] = []
    for name, dates in sorted(merged.items()):
        if name.replace(" ", "") in {e.replace(" ", "") for e in ENTITY_NAMES}:
            entity_rows.append(name)
            continue
        if not dates:
            locality_specific.append(name)
            continue
        municipality = joiner.join_despaced("28", name)
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "manual-alias" if name in ALIASES else "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Fiesta local", "sourceRecordId": f"bocm:{name}:{d}"}
                for d in dates
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError("Duplicate Madrid municipality codes")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "13"
    }
    covered = {m["ineCode"] for m in municipalities}
    if not covered <= set(roster):
        raise RuntimeError(f"Unknown codes: {covered - set(roster)}")
    omissions = []
    for code in sorted(set(roster) - covered):
        reason = OMISSION_REASON
        if code == "28162":
            reason = (
                "El BOCM publica días festivos por núcleo de población para este "
                "municipio (Valdeolmos y Alalpardo) sin un par de ámbito municipal."
            )
        omissions.append({"ineCode": code, "name": roster[code]["name"], "reason": reason})

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "13",
        "autonomousCommunity": "Comunidad de Madrid",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ("bocm-20251212-34", "bocm-20251229-19", "bocm-20260108-18")
        ],
        "auditNote": (
            f"Base + two amendment resolutions; {len(amend1)} entries in "
            f"amend1, {len(amend2)} in amend2. Local-entity rows excluded: "
            f"{', '.join(entity_rows)}."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/comunidad-de-madrid-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()