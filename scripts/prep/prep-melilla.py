#!/usr/bin/env python3
"""Normalize the Melilla 2026 local holidays.

Source: BOME 6.315 art. 1033 (03/10/2025) — Acuerdo del Consejo de Gobierno
de 19/09/2025. Local pair: 8 Sep (Virgen de la Victoria) and 17 Sep (Día de
Melilla). Calendar = 8 national + 4 city + 2 local = 14.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, load_frozen, manifest_source,  # noqa: E402
                     parse_spanish_date, write_json)


def main() -> None:
    source = manifest_source("bome-2025-1033")
    html = load_frozen("bome-2025-1033").decode("utf-8")
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)

    dates = sorted({
        d for d in (
            parse_spanish_date("8 de septiembre"),
            parse_spanish_date("17 de septiembre"),
        )
    })
    if "2026-09-08" not in dates or "2026-09-17" not in dates:
        raise RuntimeError(f"Melilla local pair not found")
    holidays = [
        {"date": "2026-09-08", "name": "Día de Nuestra Señora la Virgen de la Victoria",
         "sourceRecordId": "bome-2025-1033:2026-09-08"},
        {"date": "2026-09-17", "name": "Día de Melilla",
         "sourceRecordId": "bome-2025-1033:2026-09-17"},
    ]
    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "19",
        "autonomousCommunity": "Melilla",
        "localHolidayModel": "two-local-days",
        "sources": [{"sourceId": source["id"], "sourceSha256": source["sha256"]}],
        "auditNote": (
            "Local pair from the Consejo de Gobierno accord (BOME 6.315, art. "
            "1033); Eid dates are lunar and may be corrected after publication "
            "(re-check on refresh)."
        ),
        "municipalities": [{
            "ineCode": "52001",
            "name": "Melilla",
            "method": "native-code",
            "holidays": holidays,
        }],
        "omissions": [],
    }
    write_json(ROOT / "data/normalized/2026/local/melilla-local-holidays.json", payload)
    print("Melilla: 1 covered, 0 omitted")


if __name__ == "__main__":
    main()