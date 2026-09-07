#!/usr/bin/env python3
"""Normalize the BON 241 (02/12/2025) Navarra local-holiday resolution.

Navarra model: 12 general days (BOE matrix) + 3 December (San Francisco
Javier, common local day) + one municipal day from the annex. The annex lists
localidades (municipalities and concejos); only direct municipality entries
produce a municipal date. Descriptive dates are resolved dynamically against
the 2026 calendar (carnival, Pentecost, Ascension, ordinal weekdays).

Amendment Resolución 765/2025 (BON 1, 02/01/2026, frozen and checksum-bound)
replaces the municipal festivo of Aranguren, Bera and Cadreita and of the
concejo-only localidades Ilundain, Labiano, Laquidain (Aranguren), Mutilva,
Tajonar and Zolina (which do not produce municipal calendars here).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, load_frozen, manifest_source,  # noqa: E402
                     normalized_name, parse_spanish_date, write_json)

MONTHS_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
             "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
             "noviembre": 11, "diciembre": 12}

EASTER_2026 = date(2026, 4, 5)
SHARED_LOCAL_DAY = {"date": "2026-12-03", "name": "San Francisco Javier, Día de Navarra",
                    "sourceRecordId": "resolucion-390-2025:2026-12-03"}

# Fail-closed guard: the BON 1 amendment must land on these municipal
# calendars (the remaining amended localidades are concejo-only rows).
AMENDMENT_EXPECTED_BY_CODE = {
    "31023": "2026-06-19",  # Aranguren (was 8 de junio)
    "31064": "2026-01-19",  # Cadreita (was 12 de enero)
    "31250": "2026-08-03",  # Bera (was 3 de marzo)
}

OMISSION_REASON = (
    "La resolución oficial del BON solo fija la fiesta local de concejos para "
    "este municipio, sin fecha de ámbito municipal para 2026."
)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """n-th `weekday` (0=Mon) of the month; n=-1 = last."""
    if n < 0:
        if month == 12:
            probe = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            probe = date(year, month + 1, 1) - timedelta(days=1)
        offset = (probe.weekday() - weekday) % 7
        return probe - timedelta(days=offset)
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def resolve_descriptive(text: str) -> str | None:
    t = text.strip().lower()
    carnival_friday = EASTER_2026 - timedelta(days=51)
    carnival_monday = EASTER_2026 - timedelta(days=48)
    carnival_tuesday = EASTER_2026 - timedelta(days=47)
    pentecost_monday = EASTER_2026 + timedelta(days=50)
    ascension = EASTER_2026 + timedelta(days=39)
    if t == "lunes siguiente al primer domingo de mayo":
        return (nth_weekday(2026, 5, 6, 1) + timedelta(days=1)).isoformat()
    if t == "viernes anterior al tercer domingo de septiembre":
        return (nth_weekday(2026, 9, 6, 3) - timedelta(days=2)).isoformat()
    if t == "tercer sábado de septiembre":
        return nth_weekday(2026, 9, 5, 3).isoformat()
    if t == "segundo sábado de septiembre":
        return nth_weekday(2026, 9, 5, 2).isoformat()
    if t == "primer sábado de septiembre":
        return nth_weekday(2026, 9, 5, 1).isoformat()
    if t == "último viernes de septiembre":
        return nth_weekday(2026, 9, 4, -1).isoformat()
    if t == "tercer sábado de agosto":
        return nth_weekday(2026, 8, 5, 3).isoformat()
    if t == "primer sábado de agosto":
        return nth_weekday(2026, 8, 5, 1).isoformat()
    if t == "segundo lunes de agosto":
        return nth_weekday(2026, 8, 0, 2).isoformat()
    if t == "cuarto viernes de julio":
        return nth_weekday(2026, 7, 4, 4).isoformat()
    if t == "primer lunes de septiembre":
        return nth_weekday(2026, 9, 0, 1).isoformat()
    if t == "tercer lunes de septiembre":
        return nth_weekday(2026, 9, 0, 3).isoformat()
    if t == "primer sábado de octubre":
        return nth_weekday(2026, 10, 5, 1).isoformat()
    if t == "segundo viernes de noviembre":
        return nth_weekday(2026, 11, 4, 2).isoformat()
    if t == "viernes de la semana siguiente a san lucas":
        # San Lucas = 18 Oct; Friday of the following week.
        return nth_weekday(2026, 10, 4, 4).isoformat()
    if t == "lunes de pentecostés" or t == "segundo día de pentecostés":
        return pentecost_monday.isoformat()
    if t == "festividad de la ascensión":
        return ascension.isoformat()
    if t == "viernes de carnaval":
        return carnival_friday.isoformat()
    if t == "lunes de carnaval":
        return carnival_monday.isoformat()
    if t == "martes de carnaval":
        return carnival_tuesday.isoformat()
    return None


def parse_amendment() -> dict[str, str]:
    """Parse the Resolución 765/2025 festivo replacements from frozen BON 1.

    The resolution replaces one local day per localidad in the RESUELVO
    list: `–Name: day de month.` Returns the raw date phrase (the same
    format the BON 241 annex uses); fail closed on structural surprises.
    """
    html = load_frozen("bon-1-2026-765").decode("utf-8")
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    amendments: dict[str, str] = {}
    capturing = False
    for line in lines:
        if "sustituidas por las siguientes" in line:
            capturing = True
            continue
        if not capturing:
            continue
        if re.match(r"^\d+\.º?", line):
            break
        match = re.fullmatch(r"[–\-]\s*([^:]+):\s*(.+?)\.?\s*", line)
        if match is None:
            continue
        date_text = match.group(2).rstrip(".").strip()
        if parse_spanish_date(date_text) is None:
            raise RuntimeError(f"Unparseable BON 1 amendment date: {line}")
        amendments[match.group(1).strip()] = date_text
    if len(amendments) != 9:
        raise RuntimeError(
            f"Expected 9 BON 1 amendment localidades, found {len(amendments)}"
        )
    return amendments


def main() -> None:
    source = manifest_source("bon-241-2025")
    html = load_frozen("bon-241-2025").decode("utf-8")
    text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    start = next(i for i, l in enumerate(lines)
                 if "FIESTAS LOCALES EN LA PROVINCIA" in l)
    if start is None:
        raise RuntimeError("Navarra annex start not found")

    entries: dict[str, str] = {}
    i = start + 3
    while i + 1 < len(lines):
        name = lines[i]
        date_text = lines[i + 1]
        if re.fullmatch(r"\d{1,2} de [a-záéíóúñ]+", date_text):
            entries[name] = date_text
            i += 2
        elif name and not re.match(
            r"^(Código|Acceso|/|Navegación|Enlaces|LexNavarra|Normativa|Paseo|"
            r"848|Contacto|Aviso|Subir|Imprimir|Iniciar|Registro|Buscador|"
            r"Último|BON-Normativa|1\.|3\.|¿Cómo|&nbsp;|Boletín Oficial|31001|"
            r"bon@|Accesibilidad)", name
        ):
            entries[name] = date_text
            i += 2
        else:
            i += 1
    if len(entries) < 600:
        raise RuntimeError(f"Too few Navarra annex entries: {len(entries)}")

    # Apply Resolución 765/2025 (BON 1) replacements, last-wins by
    # accent-insensitive name (the amendment uses title case).
    amendment = parse_amendment()
    norm_entries = {normalized_name(name): name for name in entries}
    amended: set[str] = set()
    for name, date_text in amendment.items():
        target = norm_entries.get(normalized_name(name))
        if target is None:
            raise RuntimeError(
                f"BON 1 amendment localidad missing from BON 241: {name}"
            )
        entries[target] = date_text
        amended.add(target)

    joiner = RosterJoiner("31")
    joiner.add_alias("31", "URROTZ", "31244")
    municipalities: list[dict] = []
    unresolved_desc: list[str] = []
    concejo_only: list[str] = []
    for name, date_text in sorted(entries.items()):
        parenthetical = re.search(r"\(([^)]+)\)$", name)
        if parenthetical is not None:
            # Concejo row when the parenthetical names a municipality; a
            # municipality row annotated with a comarca otherwise.
            try:
                joiner.join_bilingual("31", parenthetical.group(1).strip())
                concejo_only.append(name)
                continue
            except RuntimeError:
                pass
        base = re.sub(r"\s*\(.*\)$", "", name).strip()
        try:
            municipality = joiner.join_bilingual("31", base)
        except RuntimeError:
            concejo_only.append(name)
            continue
        fixed = parse_spanish_date(date_text)
        if fixed is None:
            fixed = resolve_descriptive(date_text)
        if fixed is None:
            unresolved_desc.append(f"{name}: {date_text}")
            continue
        record_prefix = "bon1" if name in amended else "bon241"
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": name,
            "dateText": date_text,
            "holidays": [{
                "date": fixed,
                "name": "Fiesta local",
                "sourceRecordId": f"{record_prefix}:{name}:{fixed}",
            }],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Navarra codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    # Fail closed: every municipal amendment must be observable.
    by_code = {m["ineCode"]: m for m in municipalities}
    for code, expected in AMENDMENT_EXPECTED_BY_CODE.items():
        actual = by_code[code]["holidays"][0]["date"]
        if actual != expected:
            raise RuntimeError(
                f"BON 1 amendment not applied for {code}: {actual} != {expected}"
            )

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "15"
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
        "autonomousCommunityCode": "15",
        "autonomousCommunity": "Navarra",
        "localHolidayModel": "one-plus-shared",
        "sources": [
            {"sourceId": "bon-241-2025",
             "sourceSha256": manifest_source("bon-241-2025")["sha256"]},
            {"sourceId": "bon-1-2026-765",
             "sourceSha256": manifest_source("bon-1-2026-765")["sha256"]},
        ],
        "sharedLocalDay": SHARED_LOCAL_DAY,
        "auditNote": (
            "One municipal day per municipality plus the shared 3 December "
            "(San Francisco Javier) local day. Concejo-only localidades do not "
            "produce municipal dates. Amendment Resolución 765/2025 (BON 1, "
            "02/01/2026) applied: ARANGUREN 19-jun, BERA 3-ago, CADREITA "
            "19-ene replace the BON 241 dates; ILUNDÁIN, LABIANO, LAQUIDAIN "
            "(Aranguren), MUTILVA, TAJONAR, ZOLINA are amended but "
            "concejo-only and produce no municipal calendar. Unresolved "
            f"descriptive dates: {len(unresolved_desc)}."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/navarra-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted; "
          f"concejo-only {len(concejo_only)}, unresolved {len(unresolved_desc)}, "
          f"amended {len(amended)}")


if __name__ == "__main__":
    main()