#!/usr/bin/env python3
"""Normalize the Open Data Euskadi 2026 work calendar.

The dataset lists one local holiday per localidad (municipality rows plus
submunicipal barrio rows) and one territory day per territory (Álava
28/04 San Prudencio; Bizkaia and Gipuzkoa 31/07 San Ignacio). Municipalities
whose only rows are submunicipal nuclei are omitted: no municipality-wide
official day exists for them in this dataset.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, RosterJoiner, load_frozen, manifest_source, write_json  # noqa: E402

TERRITORY_PROVINCE = {"Bizkaia": "48", "Gipuzkoa": "20", "Álava - Araba": "01"}
PROVINCE_DAYS = {
    "01": {"date": "2026-04-28", "name": "San Prudencio", "sourceRecordId": "territory:alava"},
    "20": {"date": "2026-07-31", "name": "San Ignacio de Loyola", "sourceRecordId": "territory:gipuzkoa"},
    "48": {"date": "2026-07-31", "name": "San Ignacio de Loyola", "sourceRecordId": "territory:bizkaia"},
}

# Explicit aliases for bilingual INE names and dataset variants; the rest of
# the 252-name join is done through normalized-name matching (fail closed).
ALIASES = {
    ("48", "Valle de Carranza"): "48022",
    ("48", "Sopelana"): "48085",
    ("20", "Mondragón"): "20055",
    ("20", "Belaunza"): "20021",
    ("01", "Salvatierra"): "01051",
    ("01", "Arrazua-Ubarrundia"): "01008",
    ("01", "Labastida"): "01028",
    ("01", "Elvillar"): "01023",
    ("01", "Elburgo"): "01021",
    ("01", "San Millán"): "01053",
    ("01", "Ribera Baja"): "01047",
    ("01", "Ribera Alta"): "01046",
    ("01", "Villabuena de Álava"): "01057",
    ("01", "Valdegovía"): "01055",
    ("01", "Valle de Arana"): "01056",
    ("01", "Yécora"): "01060",
    ("01", "Iruña de Oca - Nanclares de la Oca"): "01901",
    ("01", "Campezo"): "01017",
    ("01", "Cripan"): "01019",
    ("01", "Lanciego"): "01032",
    ("01", "Llodio"): "01036",
    ("01", "Baños de Ebro"): "01011",
    ("01", "Moreda de Álava"): "01039",
}

OMISSION_REASON = (
    "El conjunto de datos oficial de Open Data Euskadi solo publica días "
    "locales de núcleos submunicipales para este municipio, sin día local de "
    "ámbito municipal para 2026."
)


def main() -> None:
    source = manifest_source("euskadi-calendario-laboral-2026")
    text = load_frozen("euskadi-calendario-laboral-2026").decode("utf-8")
    rows = [r for r in csv.reader(text.splitlines(), delimiter=";") if r]
    if rows[0] != ["date", "descripcionEs", "descriptionEu", "municipalityEs",
                   "MunicipalityEu", "territory", "municipalitycode",
                   "latwgs84", "lonwgs84"]:
        raise RuntimeError("Unexpected Euskadi CSV header")

    joiners: dict[str, RosterJoiner] = {}
    for territory, province in TERRITORY_PROVINCE.items():
        joiners[territory] = RosterJoiner(province)
        for (prov, name), code in ALIASES.items():
            if prov == province:
                joiners[territory].add_alias(province, name, code)

    local_by_code: dict[str, dict] = {}
    submunicipal_names: list[tuple[str, str]] = []
    for row in rows[1:]:
        if len(row) < 9:
            continue
        date, name_es = row[0], row[1]
        source_name, territory = row[3].strip(), row[5].strip()
        if not source_name or source_name in TERRITORY_PROVINCE or source_name in ("CAE", "EAE"):
            continue  # CAV-wide and territory rows are handled separately
        if territory not in TERRITORY_PROVINCE:
            raise RuntimeError(f"Unknown Euskadi territory {territory!r}")
        match = re.fullmatch(r"\d{2}/\d{2}/\d{4}", date)
        if match is None:
            raise RuntimeError(f"Bad Euskadi date {date!r}")
        iso_date = f"{date[6:10]}-{date[3:5]}-{date[0:2]}"
        joiner = joiners[territory]
        try:
            municipality = joiner.join(TERRITORY_PROVINCE[territory], source_name)
        except RuntimeError:
            submunicipal_names.append((source_name, territory))
            continue
        code = municipality["ineCode"]
        if code in local_by_code:
            raise RuntimeError(f"Duplicate local day for {code}")
        local_by_code[code] = {
            "ineCode": code,
            "name": municipality["name"],
            "method": "manual-alias" if (TERRITORY_PROVINCE[territory], source_name) in ALIASES else "normalized-name",
            "sourceName": source_name,
            "holidays": [{"date": iso_date, "name": name_es, "sourceRecordId": f"dataset:{code}:{iso_date}"}],
        }

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "16"
    }
    covered = set(local_by_code)
    if not covered <= set(roster):
        raise RuntimeError(f"Unknown codes: {covered - set(roster)}")
    omissions = [
        {"ineCode": code, "name": roster[code]["name"], "reason": OMISSION_REASON}
        for code in sorted(set(roster) - covered)
    ]

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "16",
        "autonomousCommunity": "País Vasco",
        "localHolidayModel": "one-local-plus-province",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "provinceDays": [
            {"provinceCode": prov, "date": info["date"], "name": info["name"],
             "sourceRecordId": info["sourceRecordId"]}
            for prov, info in sorted(PROVINCE_DAYS.items())
        ],
        "auditNote": (
            "One local day per municipality from the official dataset; "
            "territory days (San Prudencio / San Ignacio) as province-scope "
            "days. Submunicipal-only entries "
            f"({len(submunicipal_names)} rows) do not cover their parent "
            "municipalities."
        ),
        "municipalities": [local_by_code[c] for c in sorted(covered)],
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/pais-vasco-local-holidays.json", payload)
    print(f"{len(covered)} covered, {len(omissions)} omitted; submunicipal rows {len(submunicipal_names)}")


if __name__ == "__main__":
    main()