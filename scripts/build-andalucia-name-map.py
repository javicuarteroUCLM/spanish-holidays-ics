#!/usr/bin/env python3
"""Build the audited, fail-closed Andalucía source-name to INE-code map."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

PROVINCE_CODES = {
    "ALMERÍA": "04",
    "CÁDIZ": "11",
    "CÓRDOBA": "14",
    "GRANADA": "18",
    "HUELVA": "21",
    "JAÉN": "23",
    "MÁLAGA": "29",
    "SEVILLA": "41",
}

# These nine differences are explicit because silent fuzzy matching would make
# a source typo or a renamed municipality indistinguishable from a safe join.
MANUAL_ALIASES = {
    ("CÁDIZ", "ZAHARA DE LA SIERRA"): "11042",
    ("GRANADA", "DOMINGO PÉREZ"): "18915",
    ("GRANADA", "HUÉTOR SANTILLÁN"): "18099",
    ("GRANADA", "POLOPOS-LA MAMOLA"): "18162",
    ("HUELVA", "CORTELAZOR LA REAL"): "21026",
    ("JAÉN", "BEJÍJAR"): "23014",
    ("JAÉN", "HORNOS DE SEGURA"): "23043",
    ("MÁLAGA", "LA VIÑUELA"): "29099",
    ("SEVILLA", "ALANÍS DE LA SIERRA"): "41002",
}


def normalized_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Z0-9 ]", " ", value.upper().replace("-", " "))
    value = " ".join(value.split())
    for article in (" EL", " LA", " LOS", " LAS"):
        if value.endswith(article):
            value = f"{article.strip()} {value[: -len(article)]}"
    return value


def main() -> None:
    municipality_snapshot = json.loads(
        Path("data/normalized/2026/municipalities.json").read_text(encoding="utf-8")
    )
    municipalities = municipality_snapshot["municipalities"]
    source_rows = json.loads(
        Path("data/raw/2026/andalucia-work-calendar.json").read_text(encoding="utf-8")
    )
    local_rows = [
        row for row in source_rows if row["year"] == "2026" and row["type"] == "LOCAL"
    ]

    municipality_by_code = {entry["ineCode"]: entry for entry in municipalities}
    normalized_index: dict[tuple[str, str], list[dict[str, str]]] = {}
    for municipality in municipalities:
        key = (municipality["provinceCode"], normalized_name(municipality["name"]))
        normalized_index.setdefault(key, []).append(municipality)

    mappings = []
    source_places = sorted({(row["province"], row["municipality"]) for row in local_rows})
    for province, source_name in source_places:
        manual_code = MANUAL_ALIASES.get((province, source_name))
        if manual_code is not None:
            municipality = municipality_by_code[manual_code]
            method = "manual-alias"
        else:
            candidates = normalized_index.get(
                (PROVINCE_CODES[province], normalized_name(source_name)), []
            )
            if len(candidates) != 1:
                raise RuntimeError(
                    f"Ambiguous or missing join for {province}/{source_name}: {candidates}"
                )
            municipality = candidates[0]
            method = "normalized-name"
        mappings.append(
            {
                "province": province,
                "sourceName": source_name,
                "ineCode": municipality["ineCode"],
                "ineName": municipality["name"],
                "method": method,
            }
        )

    counts = Counter(mapping["ineCode"] for mapping in mappings)
    duplicates = [code for code, count in counts.items() if count != 1]
    if duplicates:
        raise RuntimeError(f"Multiple source municipalities map to the same INE code: {duplicates}")

    covered_codes = set(counts)
    omitted = [entry for entry in municipalities if entry["ineCode"] not in covered_codes]
    destination = Path("data/normalized/2026/andalucia-name-map.json")
    manifest = json.loads(Path("data/sources/2026/manifest.json").read_text(encoding="utf-8"))
    source = next(item for item in manifest["sources"] if item["id"] == "andalucia-work-calendar")
    destination.write_text(
        json.dumps(
            {
                "municipalitySourceSha256": municipality_snapshot["sourceSha256"],
                "localHolidaySourceSha256": source["sha256"],
                "mappings": mappings,
                "omitted": omitted,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {len(mappings)} audited mappings and {len(omitted)} omissions to {destination}"
    )


if __name__ == "__main__":
    main()
