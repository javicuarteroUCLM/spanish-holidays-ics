import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import {
  ANDALUCIA_CODE,
  TARGET_YEAR,
  assertIneCode,
  assertIsoDate,
  assertRecord,
  assertString,
  sourceById,
  type Holiday,
  type Municipality,
  type NameMap,
  type NameMapping,
  type SourceDefinition,
  type SourceManifest,
} from "./model.js";

const MANIFEST_PATH = "data/sources/2026/manifest.json";
const MUNICIPALITIES_PATH = "data/normalized/2026/municipalities.json";
const NAME_MAP_PATH = "data/normalized/2026/andalucia-name-map.json";
const BOE_HOLIDAYS_PATH = "data/normalized/2026/boe-andalucia-holidays.json";

interface RawAndaluciaHoliday {
  id: string;
  dateformat: string;
  description: string;
  municipality: string;
  province: string;
  year: string;
  type: string;
}

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
    municipality.autonomousCommunityCode !== ANDALUCIA_CODE ||
    !municipality.ineCode.startsWith(municipality.provinceCode)
  ) {
    throw new Error(
      `Invalid Andalucía municipality record: ${municipality.ineCode}`,
    );
  }
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
  if (municipalities.length !== 785) {
    throw new Error(
      `Expected 785 Andalucía municipalities, found ${municipalities.length}`,
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

function parseMapping(value: unknown, index: number): NameMapping {
  const label = `nameMap.mappings[${index}]`;
  assertRecord(value, label);
  const method = requiredString(value, "method", label);
  if (method !== "normalized-name" && method !== "manual-alias") {
    throw new Error(`Unsupported mapping method: ${method}`);
  }
  const mapping: NameMapping = {
    province: requiredString(value, "province", label),
    sourceName: requiredString(value, "sourceName", label),
    ineCode: requiredString(value, "ineCode", label),
    ineName: requiredString(value, "ineName", label),
    method,
  };
  assertIneCode(mapping.ineCode);
  return mapping;
}

export async function loadNameMap(
  root: string,
  manifest: SourceManifest,
): Promise<NameMap> {
  const raw = parseJson(
    await readFile(path.join(root, NAME_MAP_PATH), "utf8"),
    NAME_MAP_PATH,
  );
  assertRecord(raw, "name map");
  const ineSource = sourceById(manifest, "ine-municipalities-2026");
  const localSource = sourceById(manifest, "andalucia-work-calendar");
  if (
    raw.municipalitySourceSha256 !== ineSource.sha256 ||
    raw.localHolidaySourceSha256 !== localSource.sha256
  ) {
    throw new Error(
      "Name-map audit is not bound to the current frozen sources",
    );
  }
  if (!Array.isArray(raw.mappings) || !Array.isArray(raw.omitted)) {
    throw new Error("Name map must contain mappings and omissions arrays");
  }
  return {
    mappings: raw.mappings.map(parseMapping),
    omitted: raw.omitted.map(parseMunicipality),
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
  const identities = new Set<string>();
  return raw.holidays.map((value, index) => {
    const label = `boeHolidays[${index}]`;
    assertRecord(value, label);
    const date = requiredString(value, "date", label);
    const name = requiredString(value, "name", label);
    const scope = requiredString(value, "scope", label);
    if (scope !== "country" && scope !== "autonomous-community") {
      throw new Error(`Invalid BOE holiday scope: ${scope}`);
    }
    assertIsoDate(date);
    const sourceRecordId = `BOE-A-2025-21667:${date}:andalucia`;
    if (identities.has(sourceRecordId)) {
      throw new Error(`Duplicate BOE holiday identity: ${sourceRecordId}`);
    }
    identities.add(sourceRecordId);
    return {
      year: TARGET_YEAR,
      date,
      name,
      scope,
      jurisdictionCode: scope === "country" ? "ES" : ANDALUCIA_CODE,
      provenance: {
        sourceId: source.id,
        sourceRecordId,
        sourceUrl: source.documentationUrl,
      },
    };
  });
}

function parseRawAndaluciaHoliday(
  value: unknown,
  index: number,
): RawAndaluciaHoliday {
  const label = `andaluciaCalendar[${index}]`;
  assertRecord(value, label);
  return {
    id: requiredString(value, "id", label),
    dateformat: requiredString(value, "dateformat", label),
    description: requiredString(value, "description", label),
    municipality:
      typeof value.municipality === "string" ? value.municipality : "",
    province: typeof value.province === "string" ? value.province : "",
    year: requiredString(value, "year", label),
    type: requiredString(value, "type", label),
  };
}

export async function loadAndaluciaLocalHolidays(
  root: string,
  manifest: SourceManifest,
  nameMap: NameMap,
): Promise<Holiday[]> {
  const source = sourceById(manifest, "andalucia-work-calendar");
  const raw = parseJson(
    await readFile(path.join(root, source.path), "utf8"),
    source.path,
  );
  if (!Array.isArray(raw))
    throw new Error("Andalucía work calendar must be an array");
  const rows = raw
    .map(parseRawAndaluciaHoliday)
    .filter((row) => row.year === String(TARGET_YEAR) && row.type === "LOCAL");
  const mappingBySource = new Map(
    nameMap.mappings.map((mapping) => [
      `${mapping.province}\u0000${mapping.sourceName}`,
      mapping,
    ]),
  );
  if (mappingBySource.size !== nameMap.mappings.length) {
    throw new Error(
      "Audited mappings contain duplicate source municipality keys",
    );
  }
  const identities = new Set<string>();
  const holidays = rows.map((row) => {
    const mapping = mappingBySource.get(
      `${row.province}\u0000${row.municipality}`,
    );
    if (mapping === undefined) {
      throw new Error(
        `No audited INE join for ${row.province}/${row.municipality}`,
      );
    }
    const date = row.dateformat.slice(0, 10);
    assertIsoDate(date);
    const identity = `${source.id}:${row.id}`;
    if (identities.has(identity))
      throw new Error(`Duplicate source identity: ${identity}`);
    identities.add(identity);
    return {
      year: TARGET_YEAR,
      date,
      name: row.description,
      scope: "municipality" as const,
      jurisdictionCode: mapping.ineCode,
      provenance: {
        sourceId: source.id,
        sourceRecordId: row.id,
        sourceUrl: source.documentationUrl,
      },
    };
  });

  const counts = new Map<string, number>();
  for (const holiday of holidays) {
    counts.set(
      holiday.jurisdictionCode,
      (counts.get(holiday.jurisdictionCode) ?? 0) + 1,
    );
  }
  for (const mapping of nameMap.mappings) {
    if (counts.get(mapping.ineCode) !== 2) {
      throw new Error(
        `Municipality ${mapping.ineCode} does not have exactly two local holidays`,
      );
    }
  }
  if (holidays.length !== nameMap.mappings.length * 2) {
    throw new Error(
      "Local holiday rows contain an unexpected duplicate municipality join",
    );
  }
  return holidays;
}
