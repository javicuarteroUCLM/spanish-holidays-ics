#!/usr/bin/env python3
"""Normalize the DOGV 10238 (14/11/2025) CV local-holiday resolution.

Annex: `NAME: date y date [feasts].` grouped by province. Extraction artifacts
(inter-letter spaces, e.g. "DAYA NUEV A", "V ALENCIA") are handled by compact
(space-stripped) parsing. EATIM rows are not municipality calendars.
Amendment DOGV 10281 (15/01/2026) overrides Alcosser, Onil, Penàguila,
Villamalur and Benissoda (last-wins): its annex uses the "On diu / Ha de dir"
correction format, so it is parsed separately (`parse_amendment`).

Dates are extracted by a positional walk: days accumulate until the next
month word (with optional `de`/`d'` prefix) assigns them in order. Descriptive
prose that repeats a month name (e.g. Villamalur "lunes de las fiestas de
mayo; 15 de septiembre") never shifts the pairing of a later date, which is
what the old zip-style parser got wrong (it produced 2026-05-15 for
Villamalur's 15 de septiembre).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, normalized_name, write_json)

PROVINCE_BY_SECTION = {
    "RELACIÓNDEFIESTASLOCALESENLAPROVINCIADEALICANTE2026": "03",
    "RELACIÓNDEFIESTASLOCALESENLAPROVINCIADEALICANTE20262026": "03",
    "RELACIÓNDEFIESTASLOCALESENLAPROVINCIADECASTELLÓN2026": "12",
    "RELACIÓNDEFIESTASLOCALESENLAPROVINCIADECASTELLÓN20262026": "12",
    "RELACIÓNDEFIESTASLOCALESENLAPROVINCIADEVALENCIA2026": "46",
    "RELACIÓNDEFIESTASLOCALESENLAPROVINCIADEVALENCIA20262026": "46",
}
MONTHS_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
             "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
             "noviembre": 11, "diciembre": 12}
# DOGV 10281 is drafted in Valencian (Catalan month names).
MONTHS_CA = {"gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5,
             "juny": 6, "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10,
             "novembre": 11, "desembre": 12}

# DOGV 10281 section headers: `Relació de festes locals 2026 en la província
# d'Alacant: / de Castelló: / de València:` (compacted, lowercased).
AMENDMENT_PROVINCE_BY_HEADER = {
    "alacant": "03",
    "castelló": "12",
    "valència": "46",
}

# Fail-closed guard: the DOGV 10281 corrections must land on these calendars.
AMENDMENT_EXPECTED_BY_CODE = {
    "03007": {"2026-03-20", "2026-12-07"},  # Alcosser (was 20-05)
    "03096": {"2026-04-23", "2026-04-30"},  # Onil (was 28-11)
    "03103": {"2026-08-24", "2026-12-07"},  # Penàguila (was 25-08)
    "12131": {"2026-05-11", "2026-08-24"},  # Villamalur (was 15-09 base)
    "46068": {"2026-03-20", "2026-04-13"},  # Benissoda (was 20-04)
}

ALIASES = {
    "L´ALFÀSDELPÍ": "03011",
    "RAFÓLDEALMÚNIA": "03110",
    "VALLD´EBO": "03135",
    "VALLDEGALLINERA": "03136",
    "L’ALCORA": "12005",
    "LAPOBLADETORNESA": "12094",
    "LESCOVESDEVINROMÀ": "12050",
    "MONCADA/MONTCADA": "46171",
}

OMISSION_REASON = (
    "Sin par de fiestas locales en la resolución oficial del DOGV 10238 "
    "(y su modificación DOGV 10281) para 2026."
)


def extract_dates(text: str, months: dict[str, int]) -> list[str]:
    """Extract `DAY de MONTH` pairs from a spaced annex fragment.

    Month names match as whole words in the original text (so "Fiesta
    mayor" never reads as "mayo" and "13 de abril San Vicente" keeps its
    month even without punctuation). Each day is paired with the first
    month word that follows it, so descriptive prose repeating a month name
    (e.g. Villamalur "lunes de las fiestas de mayo; 15 de septiembre")
    can never shift the pairing of a later date. Digits followed by the
    ordinal indicator ("2º lunes") are not days.
    """
    lowered = text.lower()
    days: list[tuple[int, int]] = []
    for match in re.finditer(r"\d{1,2}", lowered):
        if lowered[match.end():match.end() + 1] in ("º", "°", "ª"):
            continue
        days.append((match.start(), int(match.group(0))))
    month_spans: list[tuple[int, int]] = []
    for word, num in months.items():
        for match in re.finditer(
            rf"(?<![a-zà-ÿ]){word}(?![a-zà-ÿ])", lowered
        ):
            month_spans.append((match.start(), num))
    month_spans.sort()
    dates: list[str] = []
    for day_pos, day in days:
        next_month = next(
            (num for pos, num in month_spans if pos > day_pos), None
        )
        if next_month is not None:
            dates.append(f"2026-{next_month:02d}-{day:02d}")
    return sorted(set(dates))


def parse_annex(sid: str) -> dict[str, tuple[str, list[str]]]:
    entries: dict[str, tuple[str, list[str]]] = {}
    section: str | None = None
    # Rebuild wrapped entry lines: continuation lines (no colon) append to
    # the previous line so date fragments split across lines join correctly.
    # Section headers start a new logical line.
    logical: list[str] = []
    for raw in extract_pdf(sid).splitlines():
        line = raw.strip()
        if not line or line.startswith("===") or "CVE:" in line or "Núm. 10" in line or "https://dogv" in line:
            continue
        compact_probe = re.sub(r"\s+", "", line).lower()
        is_header = any(
            compact_probe.startswith(header.lower())
            for header in PROVINCE_BY_SECTION
        )
        if ":" in line or is_header:
            logical.append(line)
        elif logical:
            logical[-1] = f"{logical[-1]} {line}"
    for raw in logical:
        compact = re.sub(r"\s+", "", raw).lower()
        if not compact:
            continue
        for header, prov in PROVINCE_BY_SECTION.items():
            if compact.startswith(header.lower()):
                section = prov
                break
        if section is None:
            continue
        if "eatim" in compact:
            continue
        if ":" not in compact:
            continue
        name, _ = compact.split(":", 1)
        name = name.upper().rstrip(".")
        if not name or len(name) > 80:
            continue
        # Parse dates from the original (spaced) rest so month words keep
        # word boundaries; the compact form is only used for name detection.
        rest = raw.split(":", 1)[1]
        dates = extract_dates(rest, MONTHS_ES)
        if not dates:
            continue
        entries[name] = (section, dates)
    return entries


def parse_amendment(sid: str) -> dict[str, tuple[str, list[str]]]:
    """Parse the DOGV 10281 "On diu / Ha de dir" correction annex.

    Each correction carries the corrected dates in the "Ha de dir" quote;
    the enclosing section header provides the province. Quotes may wrap
    across extracted lines, so the match runs on the full original text.
    Names keep their raw spelling; callers match overrides
    accent-insensitively.
    """
    full = "\n".join(
        line for line in extract_pdf(sid).splitlines()
        if not line.startswith("===")
    )
    token = re.compile(
        r"relació\s*de\s*festes\s*locals\s*2026\s*en\s*la\s*província\s*"
        r"d(?:'|e)?\s*([a-zà-ÿ]+)\s*:"
        r"|ha\s*de\s*dir\s*:\s*«([^»]+)»",
        re.IGNORECASE,
    )
    section: str | None = None
    corrections: dict[str, tuple[str, list[str]]] = {}
    for match in token.finditer(full):
        province_word, quote = match.groups()
        if province_word is not None:
            section = AMENDMENT_PROVINCE_BY_HEADER.get(
                province_word.lower()
            )
            continue
        if section is None or quote is None:
            continue
        compact_quote = re.sub(r"\s+", "", quote).lower()
        if ":" not in compact_quote:
            continue
        name, _ = compact_quote.split(":", 1)
        name = name.upper().rstrip(".")
        if not name or len(name) > 80:
            continue
        dates = extract_dates(quote, MONTHS_CA)
        if len(dates) != 2:
            continue
        corrections[name] = (section, dates)
    return corrections


def main() -> None:
    for sid in ("dogv-10238-2025", "dogv-10281-2026"):
        load_frozen(sid)
    entries = parse_annex("dogv-10238-2025")
    # Apply DOGV 10281 corrections last-wins. The amendment quotes may spell
    # names differently from the base annex (PENÀGUILA with a grave accent
    # vs PENÁGUILA with an acute), so overrides match on normalized names.
    raw_by_norm = {normalized_name(name): name for name in entries}
    amendment = parse_amendment("dogv-10281-2026")
    for name, (section, dates) in amendment.items():
        target = raw_by_norm.get(normalized_name(name))
        if target is not None:
            entries[target] = (entries[target][0], dates)
        else:
            entries[name] = (section, dates)

    joiners = {prov: RosterJoiner(prov) for prov in ("03", "12", "46")}
    for name, code in ALIASES.items():
        joiners[code[:2]].add_alias(code[:2], name, code)
    municipalities: list[dict] = []
    for name, (section, dates) in sorted(entries.items()):
        if len(dates) != 2:
            continue
        municipality = joiners[section].join_despaced(section, name)
        municipalities.append({
            "ineCode": municipality["ineCode"],
            "name": municipality["name"],
            "method": "normalized-name",
            "sourceName": name,
            "holidays": [
                {"date": d, "name": "Festa local",
                 "sourceRecordId": f"dogv:{name}:{d}"}
                for d in dates
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate CV codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    # Fail closed: every DOGV 10281 correction must be observable in the
    # normalized output, otherwise the amendment was not parsed/applied.
    by_code = {m["ineCode"]: m for m in municipalities}
    for code, expected in AMENDMENT_EXPECTED_BY_CODE.items():
        actual = {h["date"] for h in by_code[code]["holidays"]}
        if actual != expected:
            raise RuntimeError(
                f"DOGV 10281 amendment not applied for {code}: "
                f"{sorted(actual)} != {sorted(expected)}"
            )

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "10"
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
        "autonomousCommunityCode": "10",
        "autonomousCommunity": "Comunitat Valenciana",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ("dogv-10238-2025", "dogv-10281-2026")
        ],
        "auditNote": (
            "DOGV 10238 base with DOGV 10281 modifications applied "
            "(Alcosser, Onil, Penàguila, Villamalur, Benissoda). EATIM rows "
            "do not create calendars."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/comunitat-valenciana-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted; "
          f"amendment entries {len(amendment)}")


if __name__ == "__main__":
    main()