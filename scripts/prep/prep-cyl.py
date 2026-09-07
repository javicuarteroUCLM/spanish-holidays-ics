#!/usr/bin/env python3
"""Normalize Castilla y León 2026 local holidays.

Evidence layers (in priority order):
1. The nine consolidated provincial BOP announcements (September 2025),
   parsed in the audited research matrix `audit/cyl-resolution-2026.json`
   (`bop_dates`). The BOP pair wins when complete.
2. The Junta open-data API dataset (`cyl-fiestas-locales-api`), recomputed
   directly from the frozen records for this script (and cross-checked against
   the same matrix's `api_dates`). Used when the BOP pair is incomplete.
3. Municipal announcements in BOP León (`audit/cyl-municipal-2026.json`),
   which resolve 9 further municipalities with full official citations.

Disagreements between a complete BOP pair and a complete API pair are resolved
in favour of the BOP pair (the consolidated provincial announcement is the
operative publication).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, load_frozen, manifest_source, write_json  # noqa: E402

AUDIT_MATRIX = ROOT / "data/raw/2026/audit/cyl-resolution-2026.json"
AUDIT_MATRIX_SHA = "51ab8f8ea20b131eb3564f8907d5642a2ff93fd3ccf0a32c918622c120023d84"
AUDIT_MUNICIPAL = ROOT / "data/raw/2026/audit/cyl-municipal-2026.json"
AUDIT_MUNICIPAL_SHA = "7154267848fb60d748ff4c2cff91090d980848f0766d77a9a457f17f50a00733"

BOP_SOURCE_BY_PROVINCE = {
    "05": "bop-avila-2026", "09": "bop-burgos-2026", "24": "bop-leon-2026",
    "34": "bop-palencia-2026", "37": "bop-salamanca-2026",
    "40": "bop-segovia-2026", "42": "bop-soria-2026",
    "47": "bop-valladolid-2026", "49": "bop-zamora-2026",
}

OMISSION_REASON = (
    "Sin registro oficial completo de fiestas locales para 2026: ausente o "
    "incompleto en los anuncios provinciales de septiembre de 2025 (BOP) y en "
    "el conjunto de datos de la Junta de Castilla y León."
)


def iso(value: str) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", value)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    raise RuntimeError(f"Unparseable CyL date {value!r}")


def main() -> None:
    for path, expected in ((AUDIT_MATRIX, AUDIT_MATRIX_SHA), (AUDIT_MUNICIPAL, AUDIT_MUNICIPAL_SHA)):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Audit artifact checksum mismatch: {path}")

    matrix = json.loads(AUDIT_MATRIX.read_text("utf-8"))
    municipal = json.loads(AUDIT_MUNICIPAL.read_text("utf-8"))
    api_source = manifest_source("cyl-fiestas-locales-api")
    api_records = json.loads(load_frozen("cyl-fiestas-locales-api").decode("utf-8"))["results"]

    # Recompute the API side directly from the frozen records.
    api_dates_by_code: dict[str, set[str]] = defaultdict(set)
    api_names_by_code: dict[str, dict[str, str]] = defaultdict(dict)
    for record in api_records:
        code = f"{record['ine']:05d}"
        api_dates_by_code[code].add(record["fecha_fiesta"])
        api_names_by_code[code][record["fecha_fiesta"]] = record["nombre_fiesta"]

    municipalities: list[dict] = []
    disagreements: list[str] = []
    single_date: list[str] = []
    for entry in matrix["municipalities"]:
        code = entry["code"]
        bop = sorted({iso(v) for v in (entry.get("bop_dates") or []) if iso(v).startswith("2026-")})
        api = sorted(api_dates_by_code.get(code, set()))
        matrix_api = sorted({iso(v) for v in (entry.get("api_dates") or []) if iso(v).startswith("2026-")})
        if api != matrix_api:
            raise RuntimeError(
                f"API recomputation disagrees with audit matrix for {code}: "
                f"{api} vs {matrix_api}"
            )
        if len(bop) == 2:
            pair, via, source_ids = bop, "bop", [BOP_SOURCE_BY_PROVINCE[entry["cpro"]]]
            if len(api) == 2 and api != bop:
                disagreements.append(code)
        elif len(api) == 2:
            pair, via, source_ids = api, "api", [api_source["id"]]
        else:
            if len(bop) == 1 or len(api) == 1:
                single_date.append(code)
            continue
        holidays = [
            {
                "date": d,
                "name": api_names_by_code.get(code, {}).get(d) or "Fiesta local",
                "sourceRecordId": f"{via}:{d}",
            }
            for d in pair
        ]
        municipalities.append({
            "ineCode": code,
            "name": entry["name"],
            "method": "native-code",
            "evidence": via,
            "sourceIds": source_ids,
            "holidays": holidays,
        })

    # Municipal-lane resolutions (BOP León announcements).
    by_code = {m["ineCode"]: m for m in municipalities}
    municipal_resolved: list[str] = []
    for item in municipal["municipalities"]:
        if item["status"] != "resolved":
            continue
        dates = [d for d in item["dates"] if d.startswith("2026-")]
        if len(dates) != 2:
            # Matallana de Torío declares one municipality-general date only.
            continue
        code = item["code"]
        if code in by_code:
            raise RuntimeError(f"Municipal-lane code {code} already covered")
        municipalities.append({
            "ineCode": code,
            "name": item["name"],
            "method": "native-code",
            "evidence": "municipal-bop",
            "sourceIds": ["bop-leon-2026"],
            "publication": item["publication"],
            "publicationId": item["publication_id"],
            "sourceUrl": item["source_url"],
            "holidays": [
                {"date": d, "name": "Fiesta local", "sourceRecordId": f"municipal-bop:{d}"}
                for d in dates
            ],
        })
        municipal_resolved.append(code)

    municipalities.sort(key=lambda m: m["ineCode"])
    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "07"
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
        "autonomousCommunityCode": "07",
        "autonomousCommunity": "Castilla y León",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": "cyl-fiestas-locales-api", "sourceSha256": api_source["sha256"]},
            *[
                {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
                for s in sorted(set(BOP_SOURCE_BY_PROVINCE.values()))
            ],
        ],
        "auditNote": (
            "Pairs sourced from the September-2025 provincial BOP announcements "
            "when complete, else from the Junta open-data API (CC BY 4.0 ES), "
            "else from municipal BOP-León announcements. BOP wins over API on "
            f"{len(disagreements)} disagreements ({', '.join(disagreements[:6])}{'...' if len(disagreements) > 6 else ''}). "
            f"Single-date records omitted for {len(single_date)} municipalities. "
            f"Municipal lane resolved {len(municipal_resolved)}."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/castilla-y-leon-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()