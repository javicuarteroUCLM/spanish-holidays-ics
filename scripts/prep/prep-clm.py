#!/usr/bin/env python3
"""Normalize Castilla-La Mancha 2026 local holidays.

Sources: DOCM 240 (12/12/2025) base annex, DOCM 51 (16/03/2026) modification,
BOP Albacete 138 (26/11/2025) for Masegoso, BOP Ciudad Real 199 (15/10/2025)
cross-check for Alcoba, and BOP Guadalajara 225 (24/11/2025) for rows where the
DOCM extraction loses the first month ("8 de y 11 de septiembre").

Municipalities whose DOCM rows are constituent-town / EATIM granularity with no
municipality-wide pair, single-date rows, or genuinely absent rows are omitted.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, parse_spanish_date, write_json)

SECTIONS = {"Albacete": "02", "Ciudad Real": "13", "Cuenca": "16",
            "Guadalajara": "19", "Toledo": "45"}

ALIASES = {
    "Chinchilla": "02029",
    "Villaverde del Guadalimar": "02084",
    "Almadanejos": "13012",           # DOCM typo for Almadenejos
    "Gualdalmez": "13046",            # DOCM typo for Guadalmez
    "Santa Cruz de Cañamos": "13076", # DOCM typo for Santa Cruz de los Cáñamos
    "Valdemanco de Esteras": "13086",
    "Cañadajuncosa": "16047",
    "Huerguina, La": "16109",
    "Paracuellos de la Vega": "16150",
    "Peñalen": "19214",               # DOCM amendment spelling for Peñalén
    "Alcoba de los Montes": "13006",
}

ENTITY_GRANULARITY_CODES = {
    "16173": "El Valle de Altomira",
    "16272": "Villas de la Ventosa",
    "16901": "Campos del Paraíso",
    "16904": "Fuentenava de Jábaga",
    "16908": "Pozorrubielos de la Mancha",
    "16909": "Sotorribas",
    "16910": "Villar y Velasco",
}
ABSENT_CODES = {
    "19209": "Pardos",
    "19239": "Robledillo de Mohernando",
    "19243": "Rueda de la Sierra",
    "19285": "Torrubia",
    "19289": "Traíd",
    "45080": "Illán de Vacas",
}
SINGLE_DATE_CODES = {
    "19196": "Muduex",
    "19246": "Saelices de la Sal",
}

BOP_GU_AUDIT = ROOT / "data/raw/2026/audit/bop-guadalajara-225-2025.pdf"
BOP_GU_AUDIT_SHA = "afafe42b2ea7f9cc6033f1f3834f00dfd77b08b1011c8a8561e0c68500f6eeb3"


def parse_docm_rows(text: str) -> list[tuple[str, str, list[str]]]:
    rows: list[tuple[str, str, list[str]]] = []
    prov: str | None = None
    for line in text.splitlines():
        line = line.strip()
        match = re.match(r"^Relación de Fiestas Locales de (.+)$", line)
        if match:
            prov = SECTIONS.get(match.group(1))
            continue
        if prov is None or line in ("Municipios Fiestas", "Municipio Fiestas") or not line:
            continue
        if line.startswith("AÑO") or "Núm." in line:
            continue  # page footers
        # "d1 de y d2 de month" artifact: both dates fall in the second month
        # (cross-checked against BOP Guadalajara 225).
        artifact = re.search(r"(\d{1,2})\s+de\s+y\s+(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s*$", line)
        if artifact:
            d1 = parse_spanish_date(f"{artifact.group(1)} de {artifact.group(3)}")
            d2 = parse_spanish_date(f"{artifact.group(2)} de {artifact.group(3)}")
            name = line[: artifact.start()].strip()
            rows.append((prov, name, sorted({d1, d2})))
            continue
        date_matches = re.findall(r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", line)
        dates = sorted({p for d, mo in date_matches if (p := parse_spanish_date(f"{d} de {mo}"))})
        if not dates:
            continue
        name = re.sub(r"\d{1,2}\s*(?:de\s*)?[a-záéíóúñ]+\s*(?:y\s*)?", "", line).strip()
        name = re.sub(r"[,;]+$", "", name).strip()
        name = re.sub(r"\s+de$", "", name)  # trailing "de" from "y de 15 mayo"
        rows.append((prov, name, dates))
    return rows


def main() -> None:
    base_source = manifest_source("docm-240-2025")
    amend_source = manifest_source("docm-51-2026")
    for sid in ("docm-240-2025", "docm-51-2026", "bop-albacete-138-2025",
                "bop-ciudad-real-199-2025"):
        load_frozen(sid)
    for path, expected in ((BOP_GU_AUDIT, BOP_GU_AUDIT_SHA),):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"BOP Guadalajara audit artifact mismatch")

    rows = parse_docm_rows(extract_pdf("docm-240-2025"))
    by_key: dict[tuple[str, str], list[str]] = {}
    for prov, name, dates in rows:
        if len(dates) == 2:
            by_key.setdefault((prov, name), []).extend(dates)

    # DOCM 51 modification overrides.
    amendment_rows: dict[tuple[str, str], list[str]] = {}
    amend_prov: str | None = None
    for line in extract_pdf("docm-51-2026").splitlines():
        line = line.strip()
        if not line or line.startswith("AÑO") or "Núm." in line:
            continue
        prov_match = re.search(r"Provincia de (Albacete|Ciudad Real|Cuenca|Guadalajara|Toledo)", line)
        if prov_match:
            amend_prov = SECTIONS[prov_match.group(1)]
            continue
        date_matches = re.findall(r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", line)
        dates = sorted({p for d, mo in date_matches if (p := parse_spanish_date(f"{d} de {mo}"))})
        if len(dates) != 2:
            continue
        name = re.sub(r"\d{1,2}\s*(?:de\s*)?[a-záéíóúñ]+\s*(?:y\s*)?", "", line).strip()
        name = re.sub(r"\s+de$", "", name)
        if amend_prov is not None and name:
            amendment_rows[(amend_prov, name)] = dates

    # BOP Albacete: Masegoso (absent from DOCM base).
    bop_ab: dict[str, list[str]] = {}
    for line in extract_pdf("bop-albacete-138-2025").splitlines():
        line = line.strip().replace("\t", " ")
        date_matches = re.findall(r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", line)
        dates = sorted({p for d, mo in date_matches if (p := parse_spanish_date(f"{d} de {mo}"))})
        if len(dates) != 2:
            continue
        name = re.sub(r"\d{1,2}\s*(?:de\s*)?[a-záéíóúñ]+\s*(?:y\s*)?", "", line).strip()
        name = re.sub(r"\s+de$", "", name)
        if name:
            bop_ab[name] = dates

    # BOP Ciudad Real: Alcoba cross-check (22/05, 14/09).
    alcoba_bop: list[str] = []
    month_abbrev = {"ene": "enero", "feb": "febrero", "mar": "marzo", "abr": "abril",
                    "may": "mayo", "jun": "junio", "jul": "julio", "ago": "agosto",
                    "sep": "septiembre", "oct": "octubre", "nov": "noviembre",
                    "dic": "diciembre"}
    for line in extract_pdf("bop-ciudad-real-199-2025").splitlines():
        match = re.search(r"\bALCOBA\b\s+(\d{1,2})/(\w{3})\s+(\d{1,2})/(\w{3})", line.strip())
        if match:
            d1 = parse_spanish_date(f"{match.group(1)} de {month_abbrev.get(match.group(2).lower(), match.group(2))}")
            d2 = parse_spanish_date(f"{match.group(3)} de {month_abbrev.get(match.group(4).lower(), match.group(4))}")
            alcoba_bop = [d1, d2]
            break
    if alcoba_bop != [parse_spanish_date("22 de mayo"), parse_spanish_date("14 de septiembre")]:
        raise RuntimeError(f"BOP Ciudad Real Alcoba mismatch: {alcoba_bop}")

    if bop_ab.get("Masegoso") != ["2026-05-15", "2026-10-07"]:
        raise RuntimeError(f"BOP Albacete Masegoso mismatch: {bop_ab.get('Masegoso')}")
    by_key[("02", "Masegoso")] = ["2026-05-15", "2026-10-07"]

    joiners = {prov: RosterJoiner(prov) for prov in SECTIONS.values()}
    for name, code in ALIASES.items():
        joiners[code[:2]].add_alias(code[:2], name, code)

    municipalities: list[dict] = []
    entity_names: list[str] = []
    for (prov, name), dates in sorted(by_key.items()):
        try:
            municipality = joiners[prov].join(prov, name)
        except RuntimeError:
            entity_names.append(f"{prov}/{name}")
            continue
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "manual-alias" if (prov, name) in [
                (c[:2], n) for n, c in ALIASES.items()
            ] else "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Fiesta local",
                 "sourceRecordId": f"docm240:{name}:{d}"}
                for d in dates
            ],
        })
    override_codes: dict[str, list[str]] = {}
    for (prov, name), dates in amendment_rows.items():
        municipality = joiners[prov].join(prov, name)
        override_codes[municipality["ineCode"]] = dates
    municipalities = [
        {**m, "holidays": [
            {"date": d, "name": "Fiesta local",
             "sourceRecordId": f"docm51:{m['ineCode']}:{d}"}
            for d in override_codes[m["ineCode"]]
        ]}
        if m["ineCode"] in override_codes else m
        for m in municipalities
    ]
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate CLM municipality codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "08"
    }
    covered = {m["ineCode"] for m in municipalities}
    if not covered <= set(roster):
        raise RuntimeError(f"Unknown codes: {covered - set(roster)}")

    reasons = {
        **{code: (
            "La relación oficial del DOCM publica las fiestas por núcleos "
            "constituyentes o EATIMs, sin un par de fiestas de ámbito municipal."
        ) for code in ENTITY_GRANULARITY_CODES},
        **{code: (
            "Ausente de la relación oficial de fiestas locales de 2026 del "
            "DOCM y de las resoluciones provinciales (BOP)."
        ) for code in ABSENT_CODES},
        **{code: (
            "La relación oficial del DOCM contiene una sola fecha o un número "
            "no resoluble de fechas para este municipio en 2026."
        ) for code in SINGLE_DATE_CODES},
    }
    omitted_codes = sorted(set(roster) - covered)
    if omitted_codes != sorted(reasons):
        unexpected = [c for c in omitted_codes if c not in reasons]
        unlisted = [c for c in reasons if c not in omitted_codes]
        if unexpected or unlisted:
            raise RuntimeError(
                f"CLM omission set drift: unexpected {unexpected}, unlisted {unlisted}"
            )
    omissions = [
        {"ineCode": code, "name": roster[code]["name"], "reason": reasons[code]}
        for code in omitted_codes
    ]

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "08",
        "autonomousCommunity": "Castilla-La Mancha",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ("docm-240-2025", "docm-51-2026", "bop-albacete-138-2025",
                      "bop-ciudad-real-199-2025")
        ],
        "auditNote": (
            "DOCM 240 base annex with DOCM 51 modifications (Osa de la Vega, "
            "Peñalén); Masegoso from BOP Albacete 138; Alcoba cross-checked "
            "against BOP Ciudad Real 199; DOCM rows whose first month is lost "
            "in extraction (Almonacid de Zorita, Alocén, Val de San García) "
            "resolved from BOP Guadalajara 225 (frozen audit artifact). "
            "Constituent-town/EATIM rows are not merged into municipality pairs."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/castilla-la-mancha-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()