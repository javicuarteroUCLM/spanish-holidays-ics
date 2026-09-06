# Spanish municipal holidays for Google Calendar

Download a deterministic `.ics` calendar containing the 2026 public holidays
that apply to a covered municipality in Andalucía. This first release is
deliberately narrow: it publishes **774 complete calendars** and explicitly
omits **11 of the 785 Andalucía municipalities** because the frozen official
source does not contain exactly two local holiday records for them.

> This repository is a derived, non-official service. For decisions with legal
> or operational consequences, verify dates against the linked official source.

## Download a calendar

1. Open [`calendars/index.json`](calendars/index.json).
2. Find the municipality by its official five-digit INE code or name.
3. Download the file named by its `path`, for example
   `calendars/2026/andalucia/04001-abla.ics`.

Only entries in `calendars` are advertised as complete. The `omissions` array
names every Andalucía municipality for which no file is published and explains
why. No file in this release claims coverage outside Andalucía or outside 2026.

## Import into Google Calendar

On a computer, open Google Calendar, choose **Settings > Import & export >
Import**, select the downloaded `.ics` file, choose the destination calendar,
and import it. Imported files are snapshots and do not stay synchronized with
later corrections, so download a regenerated file after a source update.

Google documents the import workflow and required iCalendar envelope in its
[Calendar help](https://support.google.com/calendar/answer/37118?hl=en).

## What each calendar contains

Each calendar combines:

- 12 national and Andalucía-wide holidays from the official 2026 BOE labour
  calendar;
- exactly two local holidays from the frozen Junta de Andalucía dataset; and
- one event per date when holidays at multiple scopes overlap, while retaining
  every source record in the event description.

Events are RFC 5545 all-day events with stable identifiers, deterministic source
timestamps, UTF-8 CRLF lines, and 75-octet folding. Calendar filenames use the
INE municipality code so names can change without changing identity.

## Coverage and known gaps

| Measure                                      |   2026 value |
| -------------------------------------------- | -----------: |
| Andalucía municipalities in the INE snapshot |          785 |
| Complete calendars published                 |          774 |
| Municipalities omitted                       |           11 |
| Rest of Spain                                | Out of scope |

The primary local dataset is mutable and has received corrections after its
initial official publication. The frozen snapshot used here already reflects
the corrections visible on 6 September 2026, but later official changes require
a new source refresh and regenerated files. Source names also differ from INE
names in nine cases; those joins are explicit in
[`andalucia-name-map.json`](data/normalized/2026/andalucia-name-map.json), never
silently fuzzy-matched. The complete exclusion list appears in
[Municipios no incluidos](#municipios-no-incluidos).

## Municipios no incluidos

Los siguientes municipios andaluces **no tienen calendario publicado** en esta
versión: la fuente oficial congelada no contiene exactamente dos registros de
fiestas locales de 2026 para ellos, por lo que no hay evidencia oficial
completa disponible y no se publica un calendario que podría resultar
engañoso. Los nombres proceden del padrón municipal oficial del INE.

| Código INE | Municipio               | Provincia |
| ---------- | ----------------------- | --------- |
| 04043      | Felix                   | Almería   |
| 04060      | Lucainena de las Torres | Almería   |
| 18064      | Dehesas de Guadix       | Granada   |
| 18109      | Jete                    | Granada   |
| 18115      | Láchar                  | Granada   |
| 18185      | Ventas de Huelma        | Granada   |
| 18901      | Taha, La                | Granada   |
| 29016      | Árchez                  | Málaga    |
| 29024      | Benalauría              | Málaga    |
| 41008      | Algámitas               | Sevilla   |
| 41013      | Aznalcóllar             | Sevilla   |

## Provenance and licensing

[`data/sources/2026/manifest.json`](data/sources/2026/manifest.json) records the
exact source URL, authority, license, retrieval time, local snapshot path, and
SHA-256 for every input. Normalized files are bound to those hashes, so replacing
a raw file without re-auditing its derivation fails validation.

| Source                                                                                                                                                              | Purpose                                                 | Reuse terms                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [BOE-A-2025-21667](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-21667)                                                                                       | National and Andalucía-wide holidays                    | [AEBOE reuse conditions](https://www.boe.es/informacion/aviso_legal/index.php) |
| [INE municipality classification](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177031&idp=1254734710990)                               | Official municipality codes and names at 1 January 2026 | [CC BY 4.0](https://www.ine.es/datosabiertos/)                                 |
| [Junta de Andalucía work calendar](https://www.juntadeandalucia.es/datosabiertos/portal/dataset/calendario-de-dias-inhabiles-en-la-comunidad-autonoma-de-andalucia) | 2026 local holidays                                     | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)                      |

The generated calendars are adapted and combined data. They must not be
presented as official, endorsed, or continuously current.

## Contributor quick path

Requires maintained Node.js 22 or newer and Python 3 only for the audited INE
XLSX extraction step.

```sh
npm ci
npm run verify
```

`verify` checks formatting, lint, types, tests, generation, source checksums,
calendar structure, coverage invariants, and a second byte-for-byte rebuild.
Pull-request CI never accesses the network and fails if committed generated
files differ from a fresh build.

## Refresh official sources

Refreshing is intentionally separate from normal builds and pull-request CI:

```sh
npm run sources:check
npm run sources:refresh
python3 scripts/extract-ine-xlsx.py
python3 scripts/build-andalucia-name-map.py
```

After any BOE hash change, a maintainer must independently compare the Andalucía
column and legend with `boe-andalucia-holidays.json` before updating that file's
`sourceSha256`. Then run `npm run verify`, inspect the coverage diff, and commit
the source snapshot, derivations, documentation, and generated output together.

Adding another autonomous community means adding an isolated official-source
adapter and a measured coverage contract. It must not weaken the rule that only
municipalities with complete, unambiguous evidence receive an advertised file.
