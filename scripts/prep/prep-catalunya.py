#!/usr/bin/env python3
"""Normalize the DOGC Catalunya 2026 local-holiday calendar.

Base: Ordre EMT/208/2025 (DOGC 9565). Amendment: Ordre EMT/3/2026 (DOGC 9586),
last-wins per municipality. Municipalities with their own dated entry use it;
municipalities whose header carries no dates but whose EMD rows all share one
pair use that pair; municipalities whose EMD rows carry differing dates are
omitted (no municipality-wide pair). "Proposta no formulada" municipalities
are omitted unless a frozen municipal source proves the pair (9, tier T2).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, RosterJoiner, extract_pdf, load_frozen,  # noqa: E402
                     manifest_source, write_json)

OMISSION_REASON = (
    "El DOGC declara «proposta no formulada» para este municipio o publica "
    "sus fiestas locales únicamente a nivel de EMD con fechas distintas, sin "
    "un par de ámbito municipal demostrable para 2026."
)

MUNICIPAL_T2 = {
    "08009": {"dates": ["2026-05-25", "2026-08-04"], "name": "Argentona",
              "artifact": "cat-argentona-2026.pdf",
              "url": "https://argentona.cat/ARXIUS/plensmunicipals/2025/Certificacions/Certificat_dies_festius_Argentona_2026.pdf"},
    "08110": {"dates": ["2026-08-14", "2026-12-07"], "name": "Malgrat de Mar",
              "artifact": "cat-malgrat-2026.html",
              "url": "https://www.onamalgrat.cat/news/calendari-laboral-2026-tots-els-dies-festius-i-ponts-a-malgrat"},
    "08153": {"dates": ["2026-05-25", "2026-11-30"], "name": "Òrrius",
              "artifact": "cat-orrius-2026.html",
              "url": "https://www.orrius.cat/orrius/informacio-del-municipi/festius-locals/"},
    "08234": {"dates": ["2026-05-25", "2026-06-29"], "name": "Sant Pere de Vilamajor",
              "artifact": "cat-vilamajor-2026.html",
              "url": "https://www.vilamajor.cat/el-municipi/festius-locals"},
    "08248": {"dates": ["2026-07-24", "2026-12-10"], "name": "Santa Eulàlia de Ronçana",
              "artifact": "cat-ser-2026.html",
              "url": "https://www.ser.cat/ajuntament/informacio-oficial/calendaris"},
    "08252": {"dates": ["2026-05-25", "2026-07-06"], "name": "Barberà del Vallès",
              "artifact": "cat-bdv-2026.html",
              "url": "https://www.bdv.cat/noticies/saproven-els-dies-de-festes-locals-lany-2026"},
    "08266": {"dates": ["2026-05-04", "2026-11-11"], "name": "Cerdanyola del Vallès",
              "artifact": "cat-cerdanyola-2026.html",
              "url": "https://x.com/Cerdanyola/status/1938312493773803768"},
    "08285": {"dates": ["2026-08-01", "2026-09-21"], "name": "Torelló",
              "artifact": "cat-torello-2026.html",
              "url": "https://torello.cat"},
    "08297": {"dates": ["2026-05-15", "2026-08-22"], "name": "Veciana",
              "artifact": "cat-veciana-2026.html",
              "url": "https://www.veciana.cat//continguts//festius-locals-2026.html"},
}

MONTHS_CA = {"gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5,
             "juny": 6, "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10,
             "novembre": 11, "desembre": 12}


def extract_dates(text: str) -> list[str]:
    parts = re.split(r"\s+i\s+", text)
    dates: list[str] = []
    pending_days: list[int] = []
    for part in parts:
        days = [int(d) for d in re.findall(r"\d{1,2}", part)]
        months = []
        for m in re.findall(r"(?:de\s+|d['’])([a-zàéèíïóòúüç]+)", part.lower()):
            months.append(m)
        months = [m for m in months if m in MONTHS_CA]
        while pending_days and months:
            dates.append(f"2026-{MONTHS_CA[months[0]]:02d}-{pending_days.pop(0):02d}")
        if len(days) > len(months):
            pending_days.extend(days[: len(days) - len(months)])
            days = days[len(days) - len(months):]
        for day, month in zip(days, months):
            dates.append(f"2026-{MONTHS_CA[month]:02d}-{day:02d}")
    return sorted(set(dates))


def parse_document(sid: str) -> dict[str, dict]:
    """Return {name: {"dates": [...], "emd_rows": [[...]]}}."""
    out: dict[str, dict] = {}
    pending_header: str | None = None
    for raw_line in extract_pdf(sid).splitlines():
        is_emd = raw_line.startswith("    ")
        line = raw_line.strip()
        if not line or "proposta no formulada" in line:
            continue
        if re.search(r"\d{1,2}\s+(?:de\s+|d['’])[a-zàéèíïóòúüç]+\s+de\s+20\d{2}", line):
            continue  # signature/date-of-document lines
        date_match = re.search(r"\d{1,2}\s+(?:de\s+|d['’])[a-zàéèíïóòúüç]+", line)
        if date_match is None:
            name = line.strip("\u201c\u201d\"' “”").strip().rstrip(".").strip()
            if name and not name.isupper():
                pending_header = name
            continue
        name = line[: date_match.start()].strip().rstrip(",").strip()
        name = name.strip("\u201c\u201d\"' “”").strip()
        if not name or name.isupper():
            continue
        dates = extract_dates(line)
        if is_emd:
            if pending_header is not None:
                out.setdefault(pending_header, {"dates": [], "emd_rows": []})
                out[pending_header]["emd_rows"].append(dates)
            continue
        record = out.setdefault(name, {"dates": [], "emd_rows": []})
        record["dates"] = dates
        pending_header = None
    return out


def main() -> None:
    for sid in ("dogc-emt208-2025", "dogc-emt3-2026"):
        load_frozen(sid)
    entries = parse_document("dogc-emt208-2025")
    for name, record in parse_document("dogc-emt3-2026").items():
        if record["dates"]:
            entries.setdefault(name, {"dates": [], "emd_rows": []})
            entries[name]["dates"] = record["dates"]
            entries[name]["emd_rows"] = []
        else:
            entries.setdefault(name, {"dates": [], "emd_rows": []})
            entries[name]["emd_rows"] = record["emd_rows"]

    joiner = {prov: RosterJoiner(prov) for prov in ("08", "17", "25", "43")}
    municipalities: list[dict] = []
    emd_differing: list[str] = []
    for name, record in sorted(entries.items()):
        dates = list(record["dates"])
        if not dates and record["emd_rows"]:
            common = set()
            for row in record["emd_rows"]:
                common.update(tuple(row) for row in [row])
            common = set(tuple(r) for r in record["emd_rows"])
            if len(common) == 1:
                dates = list(common.pop())
            else:
                emd_differing.append(name)
                continue
        if len(dates) != 2:
            continue
        matched = None
        for prov, j in joiner.items():
            try:
                matched = j.join(prov, name)
                break
            except RuntimeError:
                continue
        if matched is None:
            continue
        municipalities.append({
            "ineCode": matched["ineCode"],
            "name": matched["name"],
            "method": "normalized-name",
            "sourceName": name,
            "evidence": "dogc",
            "holidays": [
                {"date": d, "name": "Festa local",
                 "sourceRecordId": f"dogc:{name}:{d}"}
                for d in dates
            ],
        })

    for code, info in MUNICIPAL_T2.items():
        artifact = ROOT / "data/raw/2026/audit" / info["artifact"]
        sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
        municipalities.append({
            "ineCode": code,
            "name": info["name"],
            "method": "native-code",
            "evidence": "municipal-t2",
            "sourceName": info["name"],
            "sourceUrl": info["url"],
            "artifactSha256": sha,
            "holidays": [
                {"date": d, "name": "Festa local",
                 "sourceRecordId": f"t2:{code}:{d}"}
                for d in info["dates"]
            ],
        })
    municipalities.sort(key=lambda m: m["ineCode"])
    codes = [m["ineCode"] for m in municipalities]
    if len(set(codes)) != len(codes):
        raise RuntimeError(f"Duplicate Catalunya codes: "
                           f"{[c for c in set(codes) if codes.count(c) > 1]}")

    roster = {
        m["ineCode"]: m
        for m in json.loads(
            (ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8")
        )["municipalities"]
        if m["autonomousCommunityCode"] == "09"
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
        "autonomousCommunityCode": "09",
        "autonomousCommunity": "Catalunya",
        "localHolidayModel": "two-local-days",
        "sources": [
            {"sourceId": s, "sourceSha256": manifest_source(s)["sha256"]}
            for s in ("dogc-emt208-2025", "dogc-emt3-2026")
        ],
        "auditNote": (
            "EMT/208/2025 with EMT/3/2026 overrides; municipalities whose EMD "
            f"rows carry differing dates: {len(emd_differing)}; 9 "
            "«proposta no formulada» municipalities resolved from frozen "
            "municipal sources (tier T2)."
        ),
        "municipalities": municipalities,
        "omissions": omissions,
    }
    write_json(ROOT / "data/normalized/2026/local/catalunya-local-holidays.json", payload)
    print(f"{len(municipalities)} covered, {len(omissions)} omitted")


if __name__ == "__main__":
    main()