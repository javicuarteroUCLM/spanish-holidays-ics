#!/usr/bin/env python3
"""Normalize the frozen Junta de Andalucía dataset into the unified format.

Reuses the audited name map already committed for Andalucía and the frozen
open-data JSON. The dataset carries exactly two LOCAL rows per municipality for
774 of 785 municipalities; the remaining 11 are recorded as omissions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, load_frozen, manifest_source, write_json  # noqa: E402


def main() -> None:
    source = manifest_source("andalucia-work-calendar")
    raw = json.loads(load_frozen("andalucia-work-calendar").decode("utf-8"))
    name_map = json.loads(
        (ROOT / "data/normalized/2026/andalucia-name-map.json").read_text("utf-8")
    )
    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "01"
    }

    by_code = {m["ineCode"]: m for m in name_map["mappings"]}
    local_rows = [
        row for row in raw
        if row["year"] == "2026" and row["type"] == "LOCAL"
    ]
    municipalities: list[dict] = []
    for code, mapping in sorted(by_code.items()):
        rows = [
            row for row in local_rows
            if f"{row['province']}\u0000{row['municipality']}"
            == f"{mapping['province']}\u0000{mapping['sourceName']}"
        ]
        if len(rows) != 2:
            raise RuntimeError(f"Expected 2 rows for {code}, found {len(rows)}")
        holidays = []
        for row in rows:
            holidays.append({
                "date": row["dateformat"][:10],
                "name": row["description"],
                "sourceRecordId": row["id"],
            })
        municipalities.append({
            "ineCode": code,
            "name": mapping["ineName"],
            "method": mapping["method"],
            "holidays": holidays,
        })

    omissions = [
        {
            "ineCode": m["ineCode"],
            "name": m["name"],
            "reason": (
                "La fuente oficial congelada (Junta de Andalucía) no contiene "
                "dos registros de fiestas locales de 2026 para este municipio."
            ),
        }
        for m in name_map["omitted"]
    ]

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "01",
        "autonomousCommunity": "Andalucía",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            "Dataset rows join the INE roster through the audited "
            "andalucia-name-map.json; exactly two LOCAL rows per municipality."
        ),
        "municipalities": municipalities,
        "omissions": sorted(omissions, key=lambda item: item["ineCode"]),
    }
    write_json(ROOT / "data/normalized/2026/local/andalucia-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()