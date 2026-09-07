#!/usr/bin/env python3
"""Normalize the Ceuta 2026 local holidays.

Source: BOCCE 6.551 (26/09/2025) — Resolución de 15/09/2025 de la Delegación
del Gobierno en Ceuta, local pair. The city's CCAA days come from the BOE
matrix (2 Abr Jueves Santo, 27 May Eidul Adha, 5 Ago Nuestra Señora de África,
2 Sep Día de Ceuta). Calendar = 8 national + 4 city + 2 local = 14.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, extract_pdf, load_frozen, manifest_source,  # noqa: E402
                     parse_spanish_date, write_json)


def main() -> None:
    source = manifest_source("bocce-6551-2025")
    text = extract_pdf("bocce-6551-2025")
    load_frozen("bocce-6551-2025")

    dates = {
        parse_spanish_date(d)
        for d in re.findall(r"Día (\d{1,2}) de ([a-záéíóúñ]+)", text.lower())
    } | {
        parse_spanish_date(f"{m.group(1)} de {m.group(2)}")
        for m in re.finditer(r"(\d{1,2}) de ([a-záéíóúñ]+)", text)
    }
    # Extract the five named days from the resolution text.
    named = re.findall(
        r"Día (\d{1,2}) de ([a-záéíóúñ]+):? [A-ZÁÉÍÓÚ]",
        text,
    )
    resolved = sorted({parse_spanish_date(f"{d} de {m}") for d, m in named})
    if "2026-03-20" not in resolved or "2026-06-13" not in resolved:
        raise RuntimeError(f"Ceuta local pair not found: {resolved}")
    holidays = [
        {"date": "2026-03-20", "name": "Eidul Fitr (Fiesta de Culminación de Ramadán)",
         "sourceRecordId": "bocce-6551:2026-03-20"},
        {"date": "2026-06-13", "name": "San Antonio",
         "sourceRecordId": "bocce-6551:2026-06-13"},
    ]
    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "18",
        "autonomousCommunity": "Ceuta",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            "Local pair from the Delegación del Gobierno resolution (BOCCE "
            "6.551); Eid dates are lunar and may be corrected after "
            "publication (re-check on refresh)."
        ),
        "municipalities": [{
            "ineCode": "51001",
            "name": "Ceuta",
            "method": "native-code",
            "holidays": holidays,
        }],
        "omissions": [],
    }
    write_json(ROOT / "data/normalized/2026/local/ceuta-local-holidays.json", payload)
    print("Ceuta: 1 covered, 0 omitted")


if __name__ == "__main__":
    main()