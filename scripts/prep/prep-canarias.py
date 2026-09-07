#!/usr/bin/env python3
"""Normalize the Canarias 2026 calendar.

Sources: BOC Decreto 61/2025 (regional + island days) and BOC Orden
6.8.2025 (88 municipalities x 2 local days). The island membership of each
municipality is an explicit audited constant (88 rows); island days come from
the decree. Model: two-local-days plus one island day per municipality.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, parse_spanish_date, write_json)

# Audited island membership (municipality INE name -> island slug).
ISLANDS = {
    "El Hierro": ["Frontera", "Pinar de El Hierro, El", "Valverde"],
    "La Palma": ["Barlovento", "Breña Alta", "Breña Baja", "Fuencaliente de la Palma",
                 "Garafía", "Llanos de Aridane, Los", "Paso, El", "Puntagorda",
                 "Puntallana", "San Andrés y Sauces", "Santa Cruz de la Palma",
                 "Tazacorte", "Tijarafe", "Villa de Mazo"],
    "La Gomera": ["Agulo", "Alajeró", "Hermigua", "San Sebastián de la Gomera",
                  "Valle Gran Rey", "Vallehermoso"],
    "Fuerteventura": ["Antigua", "Betancuria", "Oliva, La", "Pájara",
                      "Puerto del Rosario", "Tuineje"],
    "Gran Canaria": ["Agaete", "Agüimes", "Artenara", "Arucas", "Firgas", "Gáldar",
                     "Ingenio", "Mogán", "Moya", "Palmas de Gran Canaria, Las",
                     "San Bartolomé de Tirajana", "Santa Brígida",
                     "Santa Lucía de Tirajana", "Santa María de Guía de Gran Canaria",
                     "Tejeda", "Telde", "Teror", "Valsequillo de Gran Canaria",
                     "Valleseco", "Vega de San Mateo",
                     "Aldea de San Nicolás, La"],
    "Lanzarote": ["Arrecife", "Haría", "San Bartolomé", "Teguise", "Tías", "Tinajo",
                  "Yaiza"],
    "Tenerife": ["Adeje", "Arafo", "Arico", "Arona", "Buenavista del Norte",
                 "Candelaria", "Fasnia", "Garachico", "Granadilla de Abona",
                 "Guía de Isora", "Güímar", "Icod de los Vinos", "Guancha, La",
                 "Matanza de Acentejo, La", "Orotava, La", "Victoria de Acentejo, La",
                 "Realejos, Los", "Rosario, El", "Silos, Los", "Puerto de la Cruz",
                 "San Cristóbal de La Laguna", "San Juan de la Rambla",
                 "San Miguel de Abona", "Santa Cruz de Tenerife", "Santa Úrsula",
                 "Santiago del Teide", "Sauzal, El", "Tacoronte", "Tanque, El",
                 "Tegueste", "Vilaflor de Chasna"],
}

ISLAND_DAYS = {
    "El Hierro": ("2026-09-24", "Nuestra Señora de Los Reyes"),
    "Fuerteventura": ("2026-09-18", "Nuestra Señora de la Peña"),
    "Gran Canaria": ("2026-09-08", "Nuestra Señora del Pino"),
    "La Gomera": ("2026-10-05", "Nuestra Señora de Guadalupe"),
    "La Palma": ("2026-08-05", "Nuestra Señora de Las Nieves"),
    "Lanzarote": ("2026-09-15", "Nuestra Señora de Los Volcanes"),
    "Tenerife": ("2026-02-02", "Virgen de la Candelaria"),
}

ALIASES = {
    "SAN BARTOLOMÉ DE LANZAROTE": "35018",
    "SANTA LUCÍA": "35022",
    "SANTA MARÍA DE GUÍA": "35023",
    "LA FRONTERA": "38013",
    "V ALSEQUILLO": "35031",
}

OMISSION_REASON = (
    "Sin par de fiestas locales en la orden oficial del BOC (Orden de 6 de "
    "agosto de 2025) para 2026."
)


def main() -> None:
    for sid in ("boc-decreto-61-2025", "boc-orden-3029-2025"):
        load_frozen(sid)

    joiner = RosterJoiner()  # national join by name, restricted to 35/38
    island_by_code: dict[str, str] = {}
    for island, names in ISLANDS.items():
        for name in names:
            municipality = None
            for prov in ("35", "38"):
                try:
                    municipality = joiner.join_bilingual(prov, name)
                    break
                except RuntimeError:
                    continue
            if municipality is None:
                raise RuntimeError(f"Unmatched island-map name: {island}/{name}")
            island_by_code[municipality["ineCode"]] = island
    if len(island_by_code) != 88:
        raise RuntimeError(f"Canarias island map has {len(island_by_code)} entries")

    # Parse the order annex: NAME line + "N de mes: ..." lines until next name.
    entries: dict[str, list[str]] = {}
    current: str | None = None
    for line in extract_pdf("boc-orden-3029-2025").splitlines():
        line = line.strip()
        if not line or line.startswith("===") or "Boletín Oficial" in line or "núm. 165" in line:
            continue
        if re.match(r"^[A-ZÁÉÍÓÚÜÑ]+(?:[ .\'\-][A-ZÁÉÍÓÚÜÑ]+)*\.$", line):
            name = line.rstrip(".")
            if name and name.isupper():
                current = name
                continue
        if current is None:
            continue
        date_match = re.match(
            r"(\d{1,2})\s*(?:de\s+)?([a-záéíóúñ]+):", line
        )
        if date_match is None:
            continue
        date = parse_spanish_date(f"{date_match.group(1)} de {date_match.group(2)}")
        if date is None:
            raise RuntimeError(f"Bad BOC date line: {line!r}")
        entries.setdefault(current, []).append(date)

    municipalities: list[dict] = []
    municipal_joiners = {prov: RosterJoiner(prov) for prov in ("35", "38")}
    for prov, j in municipal_joiners.items():
        for alias_name, code in ALIASES.items():
            if code.startswith(prov):
                j.add_alias(prov, alias_name, code)
    for source_name, dates in sorted(entries.items()):
        if len(dates) != 2:
            raise RuntimeError(f"{source_name} has {len(dates)} local days")
        municipality = None
        for prov in ("35", "38"):
            try:
                municipality = municipal_joiners[prov].join_despaced(prov, source_name)
                break
            except RuntimeError:
                continue
        if municipality is None:
            raise RuntimeError(f"Unmatched Canarias municipality: {source_name}")
        island = island_by_code.get(municipality["ineCode"])
        if island is None:
            raise RuntimeError(f"No island for {municipality['ineCode']}")
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": source_name,
            "island": island,
            "holidays": [
                {"date": d, "name": "Fiesta local",
                 "sourceRecordId": f"boc3029:{source_name}:{d}"}
                for d in sorted(dates)
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Canarias codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "05"
    }
    covered = {m["ineCode"] for m in municipalities}
    if not covered <= set(roster):
        raise RuntimeError(f"Unknown codes: {covered - set(roster)}")
    omissions = [
        {"ineCode": code, "name": roster[code]["name"], "reason": OMISSION_REASON}
        for code in sorted(set(roster) - covered)
    ]

    island_holidays = [
        {"island": island, "name": name,
         "date": ISLAND_DAYS[island][0],
         "feast": ISLAND_DAYS[island][1],
         "ineCodes": sorted(
             code for code, i in island_by_code.items() if i == island
         )}
        for island, name in [("El Hierro", "El Hierro"), ("Fuerteventura", "Fuerteventura"),
                             ("Gran Canaria", "Gran Canaria"), ("La Gomera", "La Gomera"),
                             ("La Palma", "La Palma"), ("Lanzarote", "Lanzarote"),
                             ("Tenerife", "Tenerife")]
    ]

    payload = {
        "schemaVersion": 1,
        "year": 2026,
        "autonomousCommunityCode": "05",
        "autonomousCommunity": "Canarias",
        "localHolidayModel": "two-local-plus-island",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ("boc-decreto-61-2025", "boc-orden-3029-2025")
        ],
        "islandDays": island_holidays,
        "auditNote": (
            "Island membership is an explicit 88-row audited map; island days "
            "from Decreto 61/2025. La Graciosa shares the Lanzarote day but is "
            "a pedanía of Teguise, not a municipality."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/canarias-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()