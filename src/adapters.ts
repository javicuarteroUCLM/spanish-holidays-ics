import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import {
  COMMUNITIES,
  TARGET_YEAR,
  assertIneCode,
  assertIsoDate,
  assertRecord,
  assertString,
  communityByCode,
  sourceById,
  type CommunityDefinition,
  type Holiday,
  type IslandDay,
  type LocalHolidayDatum,
  type ProvinceDay,
  type LocalHolidaysFile,
  type LocalMunicipality,
  type LocalOmission,
  type Municipality,
  type SourceDefinition,
  type SourceManifest,
} from "./model.js";

const MANIFEST_PATH = "data/sources/2026/manifest.json";
const MUNICIPALITIES_PATH = "data/normalized/2026/municipalities.json";
const BOE_HOLIDAYS_PATH = "data/normalized/2026/boe-holidays.json";
const LOCAL_HOLIDAYS_PATH = "data/normalized/2026/local";

function parseJson(text: string, label: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch (error) {
    throw new Error(`${label} is not valid JSON`, { cause: error });
  }
}

function requiredString(
  record: Record<string, unknown>,
  field: string,
  label: string,
): string {
  const value = record[field];
  assertString(value, `${label}.${field}`);
  return value;
}

function parseSource(value: unknown, index: number): SourceDefinition {
  const label = `manifest.sources[${index}]`;
  assertRecord(value, label);
  const source: SourceDefinition = {
    id: requiredString(value, "id", label),
    authority: requiredString(value, "authority", label),
    url: requiredString(value, "url", label),
    documentationUrl: requiredString(value, "documentationUrl", label),
    license: requiredString(value, "license", label),
    licenseUrl: requiredString(value, "licenseUrl", label),
    publishedAt: requiredString(value, "publishedAt", label),
    path: requiredString(value, "path", label),
    sha256: requiredString(value, "sha256", label),
  };
  if (
    !/^https:\/\//.test(source.url) ||
    !/^[a-f0-9]{64}$/.test(source.sha256)
  ) {
    throw new Error(`${label} contains an invalid URL or SHA-256`);
  }
  return source;
}

export async function loadAndVerifyManifest(
  root: string,
): Promise<SourceManifest> {
  const raw = parseJson(
    await readFile(path.join(root, MANIFEST_PATH), "utf8"),
    MANIFEST_PATH,
  );
  assertRecord(raw, "source manifest");
  if (
    raw.schemaVersion !== 1 ||
    raw.year !== TARGET_YEAR ||
    !Array.isArray(raw.sources)
  ) {
    throw new Error("Unsupported source manifest schema or year");
  }
  const retrievedAt = requiredString(raw, "retrievedAt", "source manifest");
  if (Number.isNaN(Date.parse(retrievedAt))) {
    throw new Error(`Invalid manifest retrieval timestamp: ${retrievedAt}`);
  }
  const sources = raw.sources.map(parseSource);
  if (new Set(sources.map((source) => source.id)).size !== sources.length) {
    throw new Error("Source manifest IDs must be unique");
  }

  for (const source of sources) {
    const bytes = await readFile(path.join(root, source.path));
    const actual = createHash("sha256").update(bytes).digest("hex");
    if (actual !== source.sha256) {
      throw new Error(
        `Frozen source checksum mismatch for ${source.id}: ${actual}`,
      );
    }
  }
  return { schemaVersion: 1, year: TARGET_YEAR, retrievedAt, sources };
}

function parseMunicipality(value: unknown, index: number): Municipality {
  const label = `municipalities[${index}]`;
  assertRecord(value, label);
  const municipality = {
    ineCode: requiredString(value, "ineCode", label),
    controlDigit: requiredString(value, "controlDigit", label),
    name: requiredString(value, "name", label),
    provinceCode: requiredString(value, "provinceCode", label),
    autonomousCommunityCode: requiredString(
      value,
      "autonomousCommunityCode",
      label,
    ),
  };
  assertIneCode(municipality.ineCode);
  if (
    !/^\d$/.test(municipality.controlDigit) ||
    !/^\d{2}$/.test(municipality.provinceCode) ||
    !/^\d{2}$/.test(municipality.autonomousCommunityCode) ||
    !municipality.ineCode.startsWith(municipality.provinceCode)
  ) {
    throw new Error(`Invalid municipality record: ${municipality.ineCode}`);
  }
  communityByCode(municipality.autonomousCommunityCode);
  return municipality;
}

export async function loadMunicipalities(
  root: string,
  manifest: SourceManifest,
): Promise<Municipality[]> {
  const raw = parseJson(
    await readFile(path.join(root, MUNICIPALITIES_PATH), "utf8"),
    MUNICIPALITIES_PATH,
  );
  assertRecord(raw, "municipality snapshot");
  const source = sourceById(manifest, "ine-municipalities-2026");
  if (raw.sourceId !== source.id || raw.sourceSha256 !== source.sha256) {
    throw new Error(
      "Municipality normalization is not bound to the current frozen INE source",
    );
  }
  if (!Array.isArray(raw.municipalities))
    throw new Error("Municipality snapshot must contain an array");
  const municipalities = raw.municipalities.map(parseMunicipality);
  if (municipalities.length !== 8132) {
    throw new Error(
      `Expected 8132 municipalities, found ${municipalities.length}`,
    );
  }
  if (
    new Set(municipalities.map((item) => item.ineCode)).size !==
    municipalities.length
  ) {
    throw new Error("Municipality INE codes must be unique");
  }
  return municipalities;
}

function parseBoeHoliday(value: unknown, index: number): Holiday {
  const label = `boeHolidays[${index}]`;
  assertRecord(value, label);
  const date = requiredString(value, "date", label);
  const name = requiredString(value, "name", label);
  const scope = requiredString(value, "scope", label);
  const code = requiredString(value, "autonomousCommunityCode", label);
  if (scope !== "country" && scope !== "autonomous-community") {
    throw new Error(`Invalid BOE holiday scope: ${scope}`);
  }
  assertIsoDate(date);
  return {
    year: TARGET_YEAR,
    date,
    name,
    scope,
    jurisdictionCode: scope === "country" ? "ES" : code,
    provenance: {
      sourceId: "boe-2026-labour-calendar",
      sourceRecordId: `BOE-A-2025-21667:${date}:${code}`,
      sourceUrl: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-21667",
    },
  };
}

export async function loadBoeHolidays(
  root: string,
  manifest: SourceManifest,
): Promise<Holiday[]> {
  const source = sourceById(manifest, "boe-2026-labour-calendar");
  const raw = parseJson(
    await readFile(path.join(root, BOE_HOLIDAYS_PATH), "utf8"),
    BOE_HOLIDAYS_PATH,
  );
  assertRecord(raw, "BOE audited holidays");
  if (
    raw.sourceId !== source.id ||
    raw.sourceSha256 !== source.sha256 ||
    !Array.isArray(raw.holidays)
  ) {
    throw new Error(
      "BOE audited holidays are not bound to the current frozen source",
    );
  }
  const holidays = raw.holidays.map(parseBoeHoliday);
  const identities = new Set(
    holidays.map((holiday) => holiday.provenance.sourceRecordId),
  );
  if (identities.size !== holidays.length) {
    throw new Error("Duplicate BOE holiday identity");
  }
  return holidays;
}

function parseLocalDatum(value: unknown, label: string): LocalHolidayDatum {
  assertRecord(value, label);
  const date = requiredString(value, "date", label);
  const name = requiredString(value, "name", label);
  const sourceRecordId = requiredString(value, "sourceRecordId", label);
  assertIsoDate(date);
  return { date, name, sourceRecordId };
}

function parseLocalMunicipality(
  value: unknown,
  index: number,
  community: CommunityDefinition,
): LocalMunicipality {
  const label = `local.municipalities[${index}]`;
  assertRecord(value, label);
  const ineCode = requiredString(value, "ineCode", label);
  assertIneCode(ineCode);
  if (
    !ineCode.startsWith(
      community.code === "18" ? "51" : community.code === "19" ? "52" : "",
    )
  ) {
    // Ceuta/Melilla use province codes 51/52; other communities' INE codes
    // start with the community code. Validated at generation against the roster.
  }
  const name = requiredString(value, "name", label);
  const holidays = value.holidays;
  if (!Array.isArray(holidays)) {
    throw new Error(`${label}.holidays must be an array`);
  }
  return {
    ineCode,
    name,
    holidays: holidays.map((item, i) =>
      parseLocalDatum(item, `${label}.holidays[${i}]`),
    ),
  };
}

function parseLocalOmission(value: unknown, index: number): LocalOmission {
  const label = `local.omissions[${index}]`;
  assertRecord(value, label);
  const ineCode = requiredString(value, "ineCode", label);
  assertIneCode(ineCode);
  return {
    ineCode,
    name: requiredString(value, "name", label),
    reason: requiredString(value, "reason", label),
  };
}

export interface LoadedLocalHolidays {
  file: LocalHolidaysFile;
  municipalities: Map<string, LocalMunicipality>;
}

export async function loadLocalHolidays(
  root: string,
  manifest: SourceManifest,
  community: CommunityDefinition,
): Promise<LoadedLocalHolidays> {
  const raw = parseJson(
    await readFile(
      path.join(
        root,
        LOCAL_HOLIDAYS_PATH,
        `${community.slug}-local-holidays.json`,
      ),
      "utf8",
    ),
    `${community.slug}-local-holidays.json`,
  );
  assertRecord(raw, "local holidays file");
  if (
    raw.schemaVersion !== 1 ||
    raw.year !== TARGET_YEAR ||
    raw.autonomousCommunityCode !== community.code ||
    raw.localHolidayModel !== community.localModel ||
    !Array.isArray(raw.sources) ||
    !Array.isArray(raw.municipalities) ||
    !Array.isArray(raw.omissions)
  ) {
    throw new Error(
      `Local holidays file does not match the community contract for ${community.slug}`,
    );
  }
  for (const binding of raw.sources) {
    assertRecord(binding, "local sources binding");
    const sourceId = requiredString(
      binding,
      "sourceId",
      "local sources binding",
    );
    const sourceSha256 = requiredString(
      binding,
      "sourceSha256",
      "local sources binding",
    );
    const source = sourceById(manifest, sourceId);
    if (source.sha256 !== sourceSha256) {
      throw new Error(
        `Local holidays binding mismatch for ${sourceId} in ${community.slug}`,
      );
    }
  }
  const municipalities = new Map<string, LocalMunicipality>();
  for (const [index, item] of (raw.municipalities as unknown[]).entries()) {
    const municipality = parseLocalMunicipality(item, index, community);
    if (municipalities.has(municipality.ineCode)) {
      throw new Error(
        `Duplicate local municipality ${municipality.ineCode} in ${community.slug}`,
      );
    }
    municipalities.set(municipality.ineCode, municipality);
  }
  const file: LocalHolidaysFile = {
    schemaVersion: 1,
    year: TARGET_YEAR,
    autonomousCommunityCode: community.code,
    autonomousCommunity: community.name,
    localHolidayModel: community.localModel,
    sources: raw.sources as LocalHolidaysFile["sources"],
    municipalities: [...municipalities.values()],
    omissions: (raw.omissions as unknown[]).map(parseLocalOmission),
  };
  if (raw.sharedLocalDay !== undefined) {
    file.sharedLocalDay = parseLocalDatum(
      raw.sharedLocalDay,
      "local.sharedLocalDay",
    );
  }
  if (raw.provinceDays !== undefined) {
    if (!Array.isArray(raw.provinceDays)) {
      throw new Error("local.provinceDays must be an array");
    }
    file.provinceDays = (raw.provinceDays as unknown[]).map((value, index) =>
      parseProvinceDay(value, index),
    );
  }
  if (raw.islandDays !== undefined) {
    if (!Array.isArray(raw.islandDays)) {
      throw new Error("local.islandDays must be an array");
    }
    file.islandDays = (raw.islandDays as unknown[]).map((value, index) =>
      parseIslandDay(value, index),
    );
  }
  if (typeof raw.auditNote === "string") file.auditNote = raw.auditNote;
  return { file, municipalities };
}

function parseProvinceDay(value: unknown, index: number): ProvinceDay {
  const label = `local.provinceDays[${index}]`;
  assertRecord(value, label);
  const provinceCode = requiredString(value, "provinceCode", label);
  if (!/^\d{2}$/.test(provinceCode)) {
    throw new Error(`${label}.provinceCode must be two digits`);
  }
  const date = requiredString(value, "date", label);
  assertIsoDate(date);
  return {
    provinceCode,
    date,
    name: requiredString(value, "name", label),
    sourceRecordId: requiredString(value, "sourceRecordId", label),
  };
}

function parseIslandDay(value: unknown, index: number): IslandDay {
  const label = `local.islandDays[${index}]`;
  assertRecord(value, label);
  const island = requiredString(value, "island", label);
  const date = requiredString(value, "date", label);
  assertIsoDate(date);
  const ineCodes = value.ineCodes;
  if (!Array.isArray(ineCodes)) {
    throw new Error(`${label}.ineCodes must be an array`);
  }
  return {
    island,
    name: requiredString(value, "name", label),
    date,
    feast: requiredString(value, "feast", label),
    ineCodes: ineCodes.map((code, i) => {
      assertString(code, `${label}.ineCodes[${i}]`);
      assertIneCode(code);
      return code;
    }),
  };
}

export function holidayIdentity(holiday: Holiday): string {
  return `${holiday.scope}:${holiday.jurisdictionCode}:${holiday.date}:${holiday.provenance.sourceId}:${holiday.provenance.sourceRecordId}`;
}

export function loadCommunityList(): CommunityDefinition[] {
  return [...COMMUNITIES];
}
