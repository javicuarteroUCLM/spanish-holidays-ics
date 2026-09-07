#!/usr/bin/env python3
"""Normalize the DOE 204 (23/10/2025) Extremadura local-holiday annex.

Annex lines are `NAME.- day y day.` grouped by province. Rows that do not join
a municipality are entidades locales menores (ELMs) and are recorded in the
audit note, not merged. Municipalities with a single date are omitted.

Later 2026 amendment resolutions (all frozen and checksum-bound in this repo)
are applied last-wins in publication order over the base annex: DOE 24
(Ribera del Fresno), DOE 58 (Alcuéscar), DOE 64 + 68 (Cuacos de Yuste, the
second resolution supersedes the first), DOE 81 (Don Benito), DOE 98
(Salvatierra de Santiago) and DOE 141 (Caminomorisco).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, normalized_name, parse_spanish_date,
                     write_json)

OMISSION_REASON = (
    "Sin par completo de fiestas locales en la resolución base del DOE 204 "
    "(23/10/2025): ausente, con una sola fecha, o solo entidad local menor."
)

# Amendment resolutions in publication order; later entries win.
AMENDMENT_SOURCES = [
    "doe-24-2026-26060276",
    "doe-58-2026-26060628",
    "doe-64-2026-26060720",
    "doe-68-2026-26060780",
    "doe-81-2026-26060941",
    "doe-98-2026-26061253",
    "doe-141-2026-26061914",
]

# Fail-closed guard: the amendment chain must land on these calendars.
AMENDMENT_EXPECTED_BY_CODE = {
    "06044": {"2026-04-06", "2026-09-11"},  # Don Benito (was 7-sep)
    "06113": {"2026-05-15", "2026-09-14"},  # Ribera del Fresno (was 15-sep)
    "10010": {"2026-04-06", "2026-10-05"},  # Alcuéscar (was 21-abr/6-oct)
    "10041": {"2026-07-13", "2026-11-06"},  # Caminomorisco (was 13-nov)
    "10068": {"2026-04-13", "2026-09-14"},  # Cuacos de Yuste (amended twice)
    "10163": {"2026-04-06", "2026-07-24"},  # Salvatierra de Santiago (was 25-jul)
}

ALIASES = {
    "GARVÍN DE LA JARA": "10083",
    "MAJADAS DE TIETAR": "10114",
    "ARROYO SAN SERVÁN": "06012",
}


def parse_amendment(source_id: str) -> dict[str, tuple[str, list[str]]]:
    """Parse one DOE amendment: `Provincia de X. NAME: day de month y day de
    month.` Returns {name: (province, dates)} with raw annex spelling.
    """
    text = extract_pdf(source_id)
    current_province: str | None = None
    amendments: dict[str, tuple[str, list[str]]] = {}
    for line in text.splitlines():
        line = line.strip()
        province_match = re.match(
            r"^Provincia de (Badajoz|Cáceres)\.?-?\s*$", line
        )
        if province_match:
            current_province = {"Badajoz": "06", "Cáceres": "10"}[
                province_match.group(1)
            ]
            continue
        if current_province is None:
            continue
        match = re.fullmatch(r"(.+?):\s*(.+?)\.\s*", line)
        if match is None:
            continue
        name = " ".join(match.group(1).split())
        date_matches = re.findall(
            r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", match.group(2)
        )
        dates: list[str] = []
        for day, month in date_matches:
            parsed = parse_spanish_date(f"{day} de {month}")
            if parsed is not None:
                dates.append(parsed)
        if len(dates) == 2:
            amendments[name.upper()] = (current_province, sorted(set(dates)))
    return amendments


def main() -> None:
    source = manifest_source("doe-204-2025")
    text = extract_pdf("doe-204-2025")
    load_frozen("doe-204-2025")

    entries: list[tuple[str, str, list[str]]] = []
    current_province: str | None = None
    for line in text.splitlines():
        line = line.strip()
        province_match = re.match(r"^La provincia de (Badajoz|Cáceres)\.", line)
        if province_match:
            current_province = {"Badajoz": "06", "Cáceres": "10"}[province_match.group(1)]
            continue
        if current_province is None:
            continue
        match = re.fullmatch(r"(.+?)\.-\s*(.+?)\.\s*", line)
        if match is None:
            continue
        name = match.group(1).strip()
        name = re.sub(r"\s+\.", " ", name)  # extraction artifact "MAJADAS .DE TIETAR"
        name = " ".join(name.split())
        dates_text = match.group(2).strip()
        date_matches = re.findall(
            r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", dates_text
        )
        dates: list[str] = []
        for day, month in date_matches:
            parsed = parse_spanish_date(f"{day} de {month}")
            if parsed is not None:
                dates.append(parsed)
        entries.append((current_province, name, sorted(set(dates))))

    joiners = {prov: RosterJoiner(prov) for prov in ("06", "10")}
    for name, code in ALIASES.items():
        joiners[code[:2]].add_alias(code[:2], name, code)

    municipalities: list[dict] = []
    elm_rows: list[str] = []
    single_date: list[str] = []
    # Base two-date rows, keyed by normalized name for the amendment chain.
    base_rows: dict[str, tuple[str, str, list[str]]] = {}
    for province, name, dates in entries:
        if len(dates) != 2:
            if len(dates) == 1:
                single_date.append(name)
            else:
                elm_rows.append(name)
            continue
        base_rows[normalized_name(name)] = (province, name, dates)

    # Apply the amendment chain last-wins in publication order.
    amended_sources: list[str] = []
    for source_id in AMENDMENT_SOURCES:
        load_frozen(source_id)
        amendments = parse_amendment(source_id)
        if not amendments:
            raise RuntimeError(f"Empty DOE amendment parse for {source_id}")
        for name, (province, dates) in amendments.items():
            key = normalized_name(name)
            if key not in base_rows:
                raise RuntimeError(
                    f"DOE amendment municipality missing from base annex: {name}"
                )
            base_rows[key] = (province, name, dates)
        amended_sources.append(source_id)

    for province, name, dates in base_rows.values():
        municipality = None
        try:
            municipality = joiners[province].join(province, name)
        except RuntimeError:
            elm_rows.append(name)
            continue
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "manual-alias" if (province, name) in ALIASES else "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Fiesta local", "sourceRecordId": f"doe204:{name}:{d}"}
                for d in dates
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError("Duplicate Extremadura municipality codes")

    # Fail closed: every amendment must be observable in the output.
    by_code = {m["ineCode"]: m for m in municipalities}
    for code, expected in AMENDMENT_EXPECTED_BY_CODE.items():
        actual = {h["date"] for h in by_code[code]["holidays"]}
        if actual != expected:
            raise RuntimeError(
                f"DOE amendment chain not applied for {code}: "
                f"{sorted(actual)} != {sorted(expected)}"
            )

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "11"
    }
    covered = {m["ineCode"] for m in municipalities}
    if not covered <= set(roster):
        raise RuntimeError(f"Unknown codes: {covered - set(roster)}")
    omitted_codes = sorted(set(roster) - covered)
    if omitted_codes:
        raise RuntimeError(
            f"Extremadura roster not fully covered at base resolution: {omitted_codes}"
        )
    omissions: list[dict] = []

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "11",
        "autonomousCommunity": "Extremadura",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ["doe-204-2025", *AMENDMENT_SOURCES]
        ],
        "auditNote": (
            f"Base resolution DOE 204 (23/10/2025) with the 2026 amendment "
            f"chain applied last-wins ({', '.join(amended_sources)}): "
            "Ribera del Fresno, Alcuéscar, Cuacos de Yuste (twice), Don "
            "Benito, Salvatierra de Santiago and Caminomorisco. "
            f"{len(elm_rows)} entity rows not joined to municipalities, "
            f"{len(single_date)} single-date rows."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/extremadura-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted; elm {len(elm_rows)}, single {len(single_date)}")


if __name__ == "__main__":
    main()