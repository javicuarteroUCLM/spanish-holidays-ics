#!/usr/bin/env python3
"""Normalize the BOA 225 (20/11/2025) + BOA 56 (23/03/2026) Aragón resolutions.

Both documents list `- Municipality. date y date. [feasts]` entries per
province, with village (aldea) rows interleaved (marked with a bullet or a
parenthetical capital locality). Village rows never join the INE roster.
Municipality entries may carry a parenthetical annotation naming the capital
locality; annotations are stripped before the join. Date phrases may share a
month ("8 y 14 de septiembre").

The research matrix's 142-code gap list (verified absent with two extractors)
must be a subset of the resulting omissions; any additional omissions are
individually verified absent from both documents.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, write_json)

SECTION_PROVINCE = {"Huesca": "22", "Teruel": "44", "Zaragoza": "50"}
CHROME = ("BOLETÍN OFICIAL DE ARAGÓN", "csv:", "Número", "=== PAGE ===",
          "Página", "núm.")
MONTHS_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
             "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
             "noviembre": 11, "diciembre": 12}

ALIASES = {
    "Binaced – Valcarca": "22060",
    "Blecua-Torres": "22064",
    "Santa Cilia de Jaca": "22208",
    "Torla": "22230",
    "Peñas de Riglos": "22173",
    "Veracruz": "22246",
    "Viacamp – Litera": "22247",
    "San Martin de la Virgen del Moncayo": "50234",
    "Villalba del Perejil": "50286",
    "Vistabella de Huerva": "50295",
    "Pleitas de Jalón": "50212",
    "Santa Eulalia del Campo": "44209",
}

OMISSION_REASON = (
    "Ausente de las resoluciones oficiales BOA 225 y BOA 56 de 2026, o con una "
    "sola fecha de ámbito municipal; sin publicación municipal oficial "
    "localizada."
)


def extract_dates(rest: str) -> list[str]:
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


def parse_documents() -> list[tuple[str, str, list[str]]]:
    rows: list[tuple[str, str, list[str]]] = []
    for sid in ("boa-225-2025", "boa-56-2026"):
        text = extract_pdf(sid)
        section: str | None = None
        current: list | None = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            prov_match = re.search(
                r"provincia de (Huesca|Teruel|Zaragoza) para el año 2026",
                line, re.I,
            )
            if prov_match:
                section = SECTION_PROVINCE[prov_match.group(1)]
                continue
            if section is None or line.startswith(CHROME):
                continue
            if re.fullmatch(r"\d+", line) or "Número" in line or "Página" in line:
                continue
            entry_match = re.match(r"^[-•]\s*(.+)$", line)
            if entry_match:
                if current is not None:
                    rows.append((current[0], current[1], current[2]))
                current = [section, entry_match.group(1).strip(), []]
                continue
            if current is not None:
                current[2].append(line)
        if current is not None:
            rows.append((current[0], current[1], current[2]))
    return rows


def main() -> None:
    for sid in ("boa-225-2025", "boa-56-2026"):
        load_frozen(sid)

    municipalities: list[dict] = []
    single_date: list[str] = []
    villages: list[str] = []
    joiners = {prov: RosterJoiner(prov) for prov in SECTION_PROVINCE.values()}
    for prov_name, code in ALIASES.items():
        joiners[code[:2]].add_alias(code[:2], prov_name, code)

    raw_text = extract_pdf("boa-225-2025") + extract_pdf("boa-56-2026")

    for section, head, tail in parse_documents():
        body = " ".join([head, *tail])
        body = re.sub(r"\d{1,2} de [a-záéíóúñ]+ de 20\d{2}", " ", body)
        dates = extract_dates(body)
        name_match = re.match(r"^(.*?)\s*\d{1,2}\s", head)
        name = name_match.group(1).strip() if name_match else head
        name = name.rstrip(".")
        name = re.sub(r"\s*\((La|El|Los|Las)\)", r" \1", name)
        name = re.sub(r"\s*\([^)]*\)", "", name).strip()
        if len(dates) != 2:
            if dates:
                single_date.append(f"{name} ({len(dates)})")
            continue
        try:
            municipality = joiners[section].join(section, name)
        except RuntimeError:
            villages.append(name)
            continue
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "manual-alias" if (section, name) in ALIASES.items()
            else "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Fiesta local",
                 "sourceRecordId": f"boa:{name}:{d}"}
                for d in dates
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Aragón codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "02"
    }
    covered = {m["ineCode"] for m in municipalities}

    ne_res = json.loads(
        (ROOT / "data/raw/2026/audit/ne-resolution-2026.json").read_text("utf-8")
    )
    research_gap = {g["code"] for g in ne_res["regions"]["Aragón"]["gap"]}
    missing = set(roster) - covered
    if not research_gap <= missing:
        raise RuntimeError(
            f"Research-verified gaps not missing from parse: "
            f"{sorted(research_gap - missing)}"
        )
    extra_missing = sorted(missing - research_gap)
    # Verify extra omissions are genuinely absent from the raw text, except
    # where the name appears only in parsed single-date/village entries.
    handled_names = {
        m["sourceName"].lower() for m in municipalities
    } | {n.lower() for n in single_date} | {n.lower() for n in villages}
    for code in extra_missing:
        name = roster[code]["name"]
        tokens = [t for t in re.split(r"[\s/]+", name.lower()) if len(t) > 3]
        if name == "Asín":
            tokens = ["asin"]
        if any(any(t in h for t in tokens) for h in handled_names):
            continue
        absent = all(re.search(rf"\b{re.escape(t)}\w*", raw_text.lower()) is None
                     for t in tokens)
        if not absent:
            raise RuntimeError(f"Extra omission {code} {name} may exist in text")
    omissions = [
        {"ineCode": code, "name": roster[code]["name"], "reason": OMISSION_REASON}
        for code in sorted(missing)
    ]

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "02",
        "autonomousCommunity": "Aragón",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ("boa-225-2025", "boa-56-2026")
        ],
        "auditNote": (
            "Union of BOA 225 and its complement BOA 56. Village rows do not "
            f"create calendars ({len(villages)} rows). Single-date municipality "
            f"entries ({len(single_date)}). Omissions beyond the audited "
            f"142-code gap: {extra_missing}."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/aragon-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted "
          f"(+{len(extra_missing)} beyond research gap)")


if __name__ == "__main__":
    main()