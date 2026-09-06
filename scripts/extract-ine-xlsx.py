#!/usr/bin/env python3
"""Extract the Andalucía municipality roster from the frozen INE workbook.

The INE publishes XLSX but not a stable CSV for this classification. This script
uses only the Python standard library, handles the narrow workbook structure we
snapshot, and fails if its expected columns or the Andalucía row count change.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
EXPECTED_COLUMNS = ["CODAUTO", "CPRO", "CMUN", "DC", "NOMBRE"]
EXPECTED_ANDALUCIA_COUNT = 785


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find(f"{{{SHEET_NS}}}v")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{SHEET_NS}}}t"))
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        return shared_strings[int(value.text)]
    return value.text


def column_number(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference)
    if letters is None:
        raise ValueError(f"Invalid XLSX cell reference: {reference}")
    number = 0
    for letter in letters.group(0):
        number = number * 26 + ord(letter) - ord("A") + 1
    return number - 1


def worksheet_rows(archive: zipfile.ZipFile) -> list[list[str]]:
    shared_strings: list[str] = []
    if "xl/sharedStrings.xml" in archive.namelist():
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(node.text or "" for node in item.iter(f"{{{SHEET_NS}}}t"))
            for item in root
        ]

    sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    rows: list[list[str]] = []
    for row in sheet.iter(f"{{{SHEET_NS}}}row"):
        values = [""] * len(EXPECTED_COLUMNS)
        for cell in row.findall(f"{{{SHEET_NS}}}c"):
            index = column_number(cell.attrib["r"])
            if index < len(values):
                values[index] = cell_value(cell, shared_strings)
        rows.append(values)
    return rows


def main() -> None:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/2026/ine-municipalities.xlsx")
    destination = Path(
        sys.argv[2] if len(sys.argv) > 2 else "data/normalized/2026/municipalities.json"
    )
    with zipfile.ZipFile(source) as archive:
        rows = worksheet_rows(archive)

    if len(rows) < 3 or rows[1] != EXPECTED_COLUMNS:
        raise RuntimeError(f"Unexpected INE workbook schema: {rows[:2]}")

    municipalities = [
        {
            "ineCode": f"{province}{municipality}",
            "controlDigit": control,
            "name": name,
            "provinceCode": province,
            "autonomousCommunityCode": community.zfill(2),
        }
        for community, province, municipality, control, name in rows[2:]
        if community == "01"
    ]
    if len(municipalities) != EXPECTED_ANDALUCIA_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_ANDALUCIA_COUNT} Andalucía municipalities, found {len(municipalities)}"
        )
    if len({entry["ineCode"] for entry in municipalities}) != len(municipalities):
        raise RuntimeError("INE municipality codes are not unique")

    manifest = json.loads(Path("data/sources/2026/manifest.json").read_text(encoding="utf-8"))
    source = next(item for item in manifest["sources"] if item["id"] == "ine-municipalities-2026")
    payload = {
        "sourceId": source["id"],
        "sourceSha256": source["sha256"],
        "municipalities": municipalities,
    }
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(municipalities)} municipalities to {destination}")


if __name__ == "__main__":
    main()
