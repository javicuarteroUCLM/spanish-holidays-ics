#!/usr/bin/env python3
"""Shared helpers for the audited source-normalization scripts.

Every prep script in this directory parses a frozen raw source and writes a
normalized JSON that the TypeScript pipeline consumes. All joins against the INE
roster go through `build_joiner`, which fails closed on ambiguity: a source name
must match exactly one municipality after normalization plus the script's
explicit manual aliases. Fuzzy matching is never used for joins.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COMMUNITY_BY_CODE = {
    "01": "Andalucía", "02": "Aragón", "03": "Asturias", "04": "Illes Balears",
    "05": "Canarias", "06": "Cantabria", "07": "Castilla y León",
    "08": "Castilla-La Mancha", "09": "Cataluña", "10": "Comunitat Valenciana",
    "11": "Extremadura", "12": "Galicia", "13": "Comunidad de Madrid",
    "14": "Región de Murcia", "15": "Navarra", "16": "País Vasco",
    "17": "La Rioja", "18": "Ceuta", "19": "Melilla",
}


def load_roster() -> list[dict[str, str]]:
    snapshot = json.loads((ROOT / "data/normalized/2026/municipalities.json").read_text("utf-8"))
    return snapshot["municipalities"]


def manifest_source(source_id: str) -> dict:
    manifest = json.loads((ROOT / "data/sources/2026/manifest.json").read_text("utf-8"))
    matches = [s for s in manifest["sources"] if s["id"] == source_id]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one source {source_id}, found {len(matches)}")
    return matches[0]


def normalized_name(value: str) -> str:
    """Canonical join form: NFKD, ASCII, uppercase, particle reordering."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Z0-9 ]", " ", value.upper().replace("-", " "))
    value = " ".join(value.split())
    for article in (" EL", " LA", " LOS", " LAS", " L'"):
        if value.endswith(article):
            value = f"{article.strip()} {value[: -len(article)]}"
    return value


class RosterJoiner:
    """Maps source place names to INE codes through normalization + aliases."""

    def __init__(self, province_code: str | None = None) -> None:
        self.roster = [
            m for m in load_roster()
            if province_code is None or m["provinceCode"] == province_code
        ]
        self.index: dict[tuple[str, str], list[dict]] = {}
        self.despaced_index: dict[tuple[str, str], list[dict]] = {}
        for municipality in self.roster:
            key = (
                municipality["provinceCode"],
                normalized_name(municipality["name"]),
            )
            self.index.setdefault(key, []).append(municipality)
            despaced = key[1].replace(" ", "")
            self.despaced_index.setdefault((key[0], despaced), []).append(municipality)
        self.aliases: dict[tuple[str, str], str] = {}

    def add_alias(self, province_code: str, source_name: str, ine_code: str) -> None:
        self.aliases[(province_code, source_name)] = ine_code

    def _alias_match(self, province_code: str, source_name: str) -> dict | None:
        for key, code in self.aliases.items():
            if key[0] != province_code:
                continue
            if key[1] == source_name or key[1].replace(" ", "") == source_name.replace(" ", ""):
                matches = [m for m in self.roster if m["ineCode"] == code]
                if len(matches) != 1:
                    raise RuntimeError(f"Alias target not found: {code}")
                return matches[0]
        return None

    def join(self, province_code: str, source_name: str) -> dict:
        """Return the municipality for a source name, failing on ambiguity."""
        manual = self.aliases.get((province_code, source_name))
        if manual is not None:
            matches = [m for m in self.roster if m["ineCode"] == manual]
            if len(matches) != 1:
                raise RuntimeError(f"Alias target not found: {manual}")
            return matches[0]
        candidates = self.index.get(
            (province_code, normalized_name(source_name)), []
        )
        if len(candidates) != 1:
            raise RuntimeError(
                f"Ambiguous or missing join for {province_code}/{source_name}: "
                f"{[c['name'] for c in candidates]}"
            )
        return candidates[0]

    def join_despaced(self, province_code: str, source_name: str) -> dict:
        """Join a source name whose spaces may have been lost in extraction."""
        alias = self._alias_match(province_code, source_name)
        if alias is not None:
            return alias
        key = (province_code, normalized_name(source_name).replace(" ", ""))
        candidates = self.despaced_index.get(key, [])
        if len(candidates) != 1:
            # Bilingual slash names: match one slash part despaced.
            norm = normalized_name(source_name).replace(" ", "")
            candidates = [
                m for m in self.roster
                if norm in [
                    normalized_name(p.strip()).replace(" ", "")
                    for p in m["name"].split("/")
                ]
            ]
        if len(candidates) != 1:
            raise RuntimeError(
                f"Ambiguous or missing despaced join for "
                f"{province_code}/{source_name}: "
                f"{[c['name'] for c in candidates]}"
            )
        return candidates[0]

    def join_bilingual(self, province_code: str, source_name: str) -> dict:
        """Join a source name against slash-separated bilingual INE names."""
        try:
            return self.join(province_code, source_name)
        except RuntimeError:
            pass
        norm = normalized_name(source_name)
        matches = [
            m for m in self.roster
            if norm in [normalized_name(p.strip()) for p in m["name"].split("/")]
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Ambiguous or missing bilingual join for "
                f"{province_code}/{source_name}: "
                f"{[m['name'] for m in matches]}"
            )
        return matches[0]


MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
MONTHS_CA = {
    "gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5, "juny": 6,
    "juliol": 7, "agost": 8, "setembre": 9, "octubre": 10, "novembre": 11,
    "desembre": 12,
    # The Balears dataset mixes occasional Spanish month spellings.
    "enero": 1, "febrero": 2, "marzo": 3, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
MONTHS_GL = {
    "xaneiro": 1, "febreiro": 2, "marzo": 3, "abril": 4, "maio": 5, "xuño": 6,
    "xullo": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11,
    "decembro": 12,
}


def parse_spanish_date(text: str, year: int = 2026) -> str | None:
    """Parse a Spanish day-month phrase such as '15 de mayo' or '15 mayo'."""
    text = text.strip().lower()
    match = re.fullmatch(
        r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", text
    )
    if match is None:
        return None
    day = int(match.group(1))
    month = MONTHS_ES.get(match.group(2))
    if month is None:
        return None
    if day < 1 or day > 31:
        return None
    return f"{year}-{month:02d}-{day:02d}"


def parse_catalan_date(text: str, year: int = 2026) -> str | None:
    """Parse a Catalan day-month phrase such as '14 d'agost' or '3 de març'."""
    text = text.strip().lower()
    match = re.fullmatch(
        r"(\d{1,2})\s*(?:de\s*|d['’])?([a-zàéèíïóòúüç]+)", text
    )
    if match is None:
        return None
    day = int(match.group(1))
    month = MONTHS_CA.get(match.group(2))
    if month is None:
        return None
    if day < 1 or day > 31:
        return None
    return f"{year}-{month:02d}-{day:02d}"


def parse_galician_date(text: str, year: int = 2026) -> str | None:
    text = text.strip().lower()
    match = re.fullmatch(
        r"(\d{1,2})\s*(?:de\s*)?([a-záéíóúñ]+)", text
    )
    if match is None:
        return None
    day = int(match.group(1))
    month = MONTHS_GL.get(match.group(2))
    if month is None:
        return None
    if day < 1 or day > 31:
        return None
    return f"{year}-{month:02d}-{day:02d}"


def parse_dmy(text: str, year: int = 2026) -> str | None:
    """Parse compact 'dd/mm' or 'dd.mm' or 'dd-mm' date fragments."""
    match = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})", text.strip())
    if match is None:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    if month < 1 or month > 12 or day < 1 or day > 31:
        return None
    return f"{year}-{month:02d}-{day:02d}"


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {path}")


def load_frozen(source_id: str) -> bytes:
    source = manifest_source(source_id)
    path = ROOT / source["path"]
    import hashlib
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != source["sha256"]:
        raise RuntimeError(f"Frozen source {source_id} checksum mismatch")
    return data


def assert_dates_unique(entries: list[dict]) -> None:
    seen = set()
    for entry in entries:
        for holiday in entry.get("holidays", []):
            key = (entry["ineCode"], holiday["date"])
            if key in seen:
                raise RuntimeError(f"Duplicate date for {key}")
            seen.add(key)

def extract_pdf(source_id: str) -> str:
    """Extract text from a frozen PDF source using pypdf (venv-provided)."""
    from pypdf import PdfReader
    from io import BytesIO
    source = manifest_source(source_id)
    data = load_frozen(source_id)
    reader = PdfReader(BytesIO(data))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n=== PAGE ===\n".join(pages)
