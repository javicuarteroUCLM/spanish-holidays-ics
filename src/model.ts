export const TARGET_YEAR = 2026 as const;
export const ANDALUCIA_CODE = "01" as const;

export type JurisdictionScope =
  | "country"
  | "autonomous-community"
  | "province"
  | "island"
  | "municipality"
  | "submunicipal";

export interface SourceDefinition {
  id: string;
  authority: string;
  url: string;
  documentationUrl: string;
  license: string;
  licenseUrl: string;
  publishedAt: string;
  path: string;
  sha256: string;
}

export interface SourceManifest {
  schemaVersion: 1;
  year: number;
  retrievedAt: string;
  sources: SourceDefinition[];
}

export interface Municipality {
  ineCode: string;
  controlDigit: string;
  name: string;
  provinceCode: string;
  autonomousCommunityCode: string;
}

export interface SourceProvenance {
  sourceId: string;
  sourceRecordId: string;
  sourceUrl: string;
}

export interface Holiday {
  year: number;
  date: string;
  name: string;
  scope: JurisdictionScope;
  jurisdictionCode: string;
  provenance: SourceProvenance;
}

export interface NameMapping {
  province: string;
  sourceName: string;
  ineCode: string;
  ineName: string;
  method: "normalized-name" | "manual-alias";
}

export interface NameMap {
  mappings: NameMapping[];
  omitted: Municipality[];
}

export interface CalendarIndexEntry {
  ineCode: string;
  municipality: string;
  provinceCode: string;
  path: string;
  holidayCount: number;
  localHolidayCount: number;
  complete: boolean;
  sha256: string;
}

export interface CoverageIndex {
  schemaVersion: 1;
  year: number;
  generatedAt: string;
  status: "partial-andalucia-coverage";
  scope: "Andalucía";
  summary: {
    totalAndaluciaMunicipalities: number;
    completeCalendars: number;
    omittedMunicipalities: number;
  };
  omissions: Array<{
    ineCode: string;
    municipality: string;
    reason: string;
  }>;
  calendars: CalendarIndexEntry[];
  sources: Array<
    Pick<
      SourceDefinition,
      "id" | "authority" | "url" | "license" | "licenseUrl" | "sha256"
    >
  >;
  disclaimer: string;
}

export function assertRecord(
  value: unknown,
  label: string,
): asserts value is Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
}

export function assertString(
  value: unknown,
  label: string,
): asserts value is string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`${label} must be a non-empty string`);
  }
}

export function assertIsoDate(value: string, year = TARGET_YEAR): void {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !value.startsWith(`${year}-`)) {
    throw new Error(`Date must be an ISO date in ${year}: ${value}`);
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  if (
    Number.isNaN(parsed.valueOf()) ||
    parsed.toISOString().slice(0, 10) !== value
  ) {
    throw new Error(`Invalid calendar date: ${value}`);
  }
}

export function assertIneCode(value: string): void {
  if (!/^\d{5}$/.test(value)) {
    throw new Error(`Invalid five-digit INE municipality code: ${value}`);
  }
}

export function sourceById(
  manifest: SourceManifest,
  id: string,
): SourceDefinition {
  const matches = manifest.sources.filter((source) => source.id === id);
  if (matches.length !== 1) {
    throw new Error(
      `Expected exactly one source named ${id}, found ${matches.length}`,
    );
  }
  return matches[0] as SourceDefinition;
}
