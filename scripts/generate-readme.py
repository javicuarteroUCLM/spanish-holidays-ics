#!/usr/bin/env python3
"""Regenerate README.md from the generated coverage index.

The user-facing coverage and omission sections are Spanish; the contributor
sections are English. Run after `npm run generate`.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    index = json.loads(
        (ROOT / "calendars/index.json").read_text("utf-8")
    )
    manifest = json.loads(
        (ROOT / "data/sources/2026/manifest.json").read_text("utf-8")
    )
    communities = index["summary"]["communities"]
    community_names = {
        code: name
        for name, code in [
            ("Andalucía", "01"), ("Aragón", "02"), ("Asturias", "03"),
            ("Illes Balears", "04"), ("Canarias", "05"), ("Cantabria", "06"),
            ("Castilla y León", "07"), ("Castilla-La Mancha", "08"),
            ("Cataluña", "09"), ("Comunitat Valenciana", "10"),
            ("Extremadura", "11"), ("Galicia", "12"),
            ("Comunidad de Madrid", "13"), ("Región de Murcia", "14"),
            ("Navarra", "15"), ("País Vasco", "16"), ("La Rioja", "17"),
            ("Ceuta", "18"), ("Melilla", "19"),
        ]
    }

    by_community: dict[str, list[dict]] = defaultdict(list)
    for omission in index["omissions"]:
        by_community[omission["autonomousCommunityCode"]].append(omission)

    lines: list[str] = []
    add = lines.append

    add("# Calendarios de fiestas locales municipales de España 2026 (ICS)")
    add("")
    add(
        "Descarga un calendario `.ics` determinista con las fiestas laborales de 2026 "
        "de cualquier municipio español cubierto. Esta versión publica "
        f"**{index['summary']['completeCalendars']:,} calendarios completos** de los "
        f"**{index['summary']['totalMunicipalities']:,} municipios** del padrón INE de "
        f"2026 y declara explícitamente los **{index['summary']['omittedMunicipalities']:,} "
        "municipios sin calendario** y el motivo de cada omisión."
    )
    add("")
    add(
        "> Este repositorio es un servicio derivado y no oficial. Para decisiones con "
        "consecuencias legales u operativas, verifica las fechas en las publicaciones "
        "oficiales enlazadas."
    )
    add("")
    add("## Descargar un calendario")
    add("")
    add("1. Abre [`calendars/index.json`](calendars/index.json).")
    add("2. Localiza el municipio por su código INE oficial de cinco dígitos o por su nombre.")
    add("3. Descarga el archivo indicado por su `path`; por ejemplo, "
        "`calendars/2026/andalucia/04001-abla.ics`.")
    add("")
    add(
        "Solo las entradas de `calendars` se anuncian como completas. El array "
        "`omissions` nombra cada municipio sin archivo publicado y explica el motivo, "
        "agrupado por comunidad autónoma."
    )
    add("")
    add("## Importar en Google Calendar")
    add("")
    add(
        "En un ordenador, abre Google Calendar y elige **Configuración > Importar y "
        "exportar > Importar**, selecciona el archivo `.ics` descargado, elige el "
        "calendario de destino e impórtalo. Los archivos importados son instantáneas y "
        "no se sincronizan con correcciones posteriores; descarga de nuevo el archivo "
        "regenerado tras una actualización de las fuentes."
    )
    add("")
    add(
        "Google documenta el flujo de importación y el envoltorio iCalendar exigido en "
        "su [ayuda de Calendar](https://support.google.com/calendar/answer/37118?hl=es)."
    )
    add("")
    add("## Qué contiene cada calendario")
    add("")
    add(
        "Cada calendario combina las fiestas no locales del territorio (nacionales y de "
        "la comunidad autónoma, del calendario oficial del BOE) con las fiestas locales "
        "del municipio publicadas por la fuente oficial de su comunidad. Según el "
        "modelo legal de cada comunidad, se añaden el día insular (Canarias), el día de "
        "territorio (País Vasco) o el día común de San Francisco Javier (Navarra)."
    )
    add("")
    add(
        "Los eventos son de día completo RFC 5545 con identificadores estables, "
        "marcas de tiempo deterministas, líneas UTF-8 CRLF y plegado de 75 octetos. "
        "Los nombres de archivo usan el código INE para que un cambio de nombre no "
        "cambie la identidad."
    )
    add("")
    add("## Cobertura y lagunas conocidas")
    add("")
    add("| Medida | Valor 2026 |")
    add("| --- | --- |")
    add(f"| Municipios de España en el padrón INE | {index['summary']['totalMunicipalities']:,} |")
    add(f"| Calendarios completos publicados | {index['summary']['completeCalendars']:,} |")
    add(f"| Municipios omitidos | {index['summary']['omittedMunicipalities']:,} |")
    for slug, coverage in sorted(communities.items()):
        add(
            f"| {community_names[coverage_name(slug, community_names)]} "
            f"(`{slug}`) | {coverage['complete']:,}/{coverage['total']:,} "
            f"({coverage['omitted']} omitidos) |"
        )
    add("")
    add(
        "Las fuentes primarias son mutables y reciben correcciones durante el año "
        "(cadenas de resoluciones de modificación en varios boletines). Las "
        "instantáneas congeladas reflejan el estado documentado de cada fuente; "
        "cambios oficiales posteriores requieren una actualización de fuentes y una "
        "regeneración. Los nombres de las fuentes pueden diferir de los nombres INE; "
        "todas las uniones son explícitas y auditadas, nunca emparejadas de forma "
        "difusa. Las listas completas de exclusiones aparecen en "
        "[Municipios no incluidos](#municipios-no-incluidos)."
    )
    add("")
    add("## Municipios no incluidos")
    add("")
    add(
        "Los municipios siguientes **no tienen calendario publicado**: la evidencia "
        "oficial congelada no contiene un par completo de fiestas locales de ámbito "
        "municipal para 2026 (el pleno no comunicó propuesta, la resolución publica "
        "solo fechas de pedanías o núcleos con fechas distintas, o la fecha es "
        "«sin determinar»). No se publica un calendario que podría resultar "
        "engañoso. Los nombres proceden del padrón municipal oficial del INE."
    )
    add("")
    for code in sorted(by_community):
        omissions = sorted(by_community[code], key=lambda o: o["ineCode"])
        add(f"### {community_names[code]}")
        add("")
        reasons = sorted({o["reason"] for o in omissions})
        for reason in reasons:
            add(f"- Motivo: {reason}")
        add("")
        add("| Código INE | Municipio |")
        add("| --- | --- |")
        for omission in omissions:
            add(f"| {omission['ineCode']} | {omission['municipality']} |")
        add("")
    add("## Procedencia y licencias")
    add("")
    add(
        "`data/sources/2026/manifest.json` registra la URL exacta, autoridad, "
        "licencia, hora de descarga, ruta local y SHA-256 de cada entrada. Los "
        "archivos normalizados están vinculados a esos hashes, de modo que sustituir "
        "un archivo original sin auditar su derivación hace fallar la validación."
    )
    add("")
    add("| Fuente | Uso | Reutilización |")
    add("| --- | --- | --- |")
    for source in manifest["sources"]:
        add(
            f"| [{source['id']}]({source['documentationUrl'] or source['url']}) "
            f"| {source['authority']} | {source['license']} |"
        )
    add("")
    add(
        "Los calendarios generados son datos adaptados y combinados. No deben "
        "presentarse como oficiales, avalados ni continuamente actualizados."
    )
    add("")
    add("## Ruta rápida para colaboradores")
    add("")
    add("Requiere Node.js 22 o posterior y Python 3 solo para los pasos de extracción auditada.")
    add("")
    add("```sh")
    add("npm ci")
    add("npm run verify")
    add("```")
    add("")
    add(
        "`verify` comprueba formato, lint, tipos, tests, generación, sumas de "
        "comprobación de fuentes, estructura de calendarios, invariantes de cobertura "
        "y una segunda reconstrucción byte a byte. El CI de pull-request no accede a "
        "la red y falla si los archivos generados confirmados difieren de una "
        "construcción nueva."
    )
    add("")
    add("## Actualizar las fuentes oficiales")
    add("")
    add("La actualización está deliberadamente separada de las construcciones normales y del CI:")
    add("")
    add("```sh")
    add("npm run sources:check")
    add("npm run sources:refresh")
    add("python3 scripts/extract-ine-xlsx.py")
    add("python3 scripts/prep/prep-boe.py")
    add("python3 scripts/prep/prep-<comunidad>.py   # por comunidad")
    add("npm run verify")
    add("```")
    add("")
    add(
        "Tras cualquier cambio de hash, un mantenedor debe comparar de forma "
        "independiente los archivos normalizados afectados con la nueva instantánea "
        "antes de actualizar su `sourceSha256`. Después ejecute `npm run verify`, "
        "revise el diff de cobertura y confirme juntos la instantánea, las "
        "derivaciones, la documentación y la salida generada."
    )
    add("")
    add(
        "Añadir otra comunidad autónoma significa añadir un adaptador aislado de "
        "fuente oficial y un contrato de cobertura medido. No debe debilitar la regla "
        "de que solo los municipios con evidencia completa e inequívoca reciben un "
        "archivo anunciado."
    )
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"README regenerado: {len(lines)} líneas")


def coverage_name(slug: str, names: dict[str, str]) -> str:
    code_by_slug = {
        "andalucia": "01", "aragon": "02", "asturias": "03", "illes-balears": "04",
        "canarias": "05", "cantabria": "06", "castilla-y-leon": "07",
        "castilla-la-mancha": "08", "catalunya": "09", "comunitat-valenciana": "10",
        "extremadura": "11", "galicia": "12", "comunidad-de-madrid": "13",
        "region-de-murcia": "14", "navarra": "15", "pais-vasco": "16",
        "la-rioja": "17", "ceuta": "18", "melilla": "19",
    }
    return code_by_slug[slug]


if __name__ == "__main__":
    main()