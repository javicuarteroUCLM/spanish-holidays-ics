export const TARGET_YEAR = 2026 as const;

export type JurisdictionScope =
  | "country"
  | "autonomous-community"
  | "province"
  | "island"
  | "municipality"
  | "submunicipal";

export type LocalHolidayModel =
  | "two-local-days"
  | "one-local-plus-province"
  | "two-local-plus-island"
  | "one-plus-shared";

export interface CommunityDefinition {
  code: string;
  slug: string;
  name: string;
  localModel: LocalHolidayModel;
}

// Stable ASCII directory slugs for every autonomous community with a
// calendar directory. Generation fails closed for any code without a
// registered slug, so a new community requires an explicit mapping.
export const COMMUNITIES: readonly CommunityDefinition[] = [
  {
    code: "01",
    slug: "andalucia",
    name: "Andalucía",
    localModel: "two-local-days",
  },
  { code: "02", slug: "aragon", name: "Aragón", localModel: "two-local-days" },
  {
    code: "03",
    slug: "asturias",
    name: "Asturias",
    localModel: "two-local-days",
  },
  {
    code: "04",
    slug: "illes-balears",
    name: "Illes Balears",
    localModel: "two-local-days",
  },
  {
    code: "05",
    slug: "canarias",
    name: "Canarias",
    localModel: "two-local-plus-island",
  },
  {
    code: "06",
    slug: "cantabria",
    name: "Cantabria",
    localModel: "two-local-days",
  },
  {
    code: "07",
    slug: "castilla-y-leon",
    name: "Castilla y León",
    localModel: "two-local-days",
  },
  {
    code: "08",
    slug: "castilla-la-mancha",
    name: "Castilla-La Mancha",
    localModel: "two-local-days",
  },
  {
    code: "09",
    slug: "catalunya",
    name: "Cataluña",
    localModel: "two-local-days",
  },
  {
    code: "10",
    slug: "comunitat-valenciana",
    name: "Comunitat Valenciana",
    localModel: "two-local-days",
  },
  {
    code: "11",
    slug: "extremadura",
    name: "Extremadura",
    localModel: "two-local-days",
  },
  {
    code: "12",
    slug: "galicia",
    name: "Galicia",
    localModel: "two-local-days",
  },
  {
    code: "13",
    slug: "comunidad-de-madrid",
    name: "Comunidad de Madrid",
    localModel: "two-local-days",
  },
  {
    code: "14",
    slug: "region-de-murcia",
    name: "Región de Murcia",
    localModel: "two-local-days",
  },
  {
    code: "15",
    slug: "navarra",
    name: "Navarra",
    localModel: "one-plus-shared",
  },
  {
    code: "16",
    slug: "pais-vasco",
    name: "País Vasco",
    localModel: "one-local-plus-province",
  },
  {
    code: "17",
    slug: "la-rioja",
    name: "La Rioja",
    localModel: "two-local-days",
  },
  { code: "18", slug: "ceuta", name: "Ceuta", localModel: "two-local-days" },
  {
    code: "19",
    slug: "melilla",
    name: "Melilla",
    localModel: "two-local-days",
  },
];

export function communityByCode(code: string): CommunityDefinition {
  const match = COMMUNITIES.find((community) => community.code === code);
  if (match === undefined) {
    throw new Error(`Unknown autonomous community code: ${code}`);
  }
  return match;
}

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

export interface LocalHolidayDatum {
  date: string;
  name: string;
  sourceRecordId: string;
}

export interface LocalMunicipality {
  ineCode: string;
  name: string;
  holidays: LocalHolidayDatum[];
}

export interface LocalOmission {
  ineCode: string;
  name: string;
  reason: string;
}

export interface ProvinceDay {
  provinceCode: string;
  date: string;
  name: string;
  sourceRecordId: string;
}

export interface IslandDay {
  island: string;
  name: string;
  date: string;
  feast: string;
  ineCodes: string[];
}

export interface LocalHolidaysFile {
  schemaVersion: 1;
  year: number;
  autonomousCommunityCode: string;
  autonomousCommunity: string;
  localHolidayModel: LocalHolidayModel;
  sources: Array<{ sourceId: string; sourceSha256: string }>;
  sharedLocalDay?: LocalHolidayDatum;
  provinceDays?: ProvinceDay[];
  islandDays?: IslandDay[];
  municipalities: LocalMunicipality[];
  omissions: LocalOmission[];
  auditNote?: string;
}

export interface CalendarIndexEntry {
  ineCode: string;
  municipality: string;
  provinceCode: string;
  autonomousCommunityCode: string;
  autonomousCommunity: string;
  path: string;
  holidayCount: number;
  localHolidayCount: number;
  complete: boolean;
  sha256: string;
}

export interface CommunityCoverage {
  total: number;
  complete: number;
  omitted: number;
}

export interface CoverageIndex {
  schemaVersion: 2;
  year: number;
  generatedAt: string;
  status: "national-partial-coverage";
  scope: "España";
  summary: {
    totalMunicipalities: number;
    completeCalendars: number;
    omittedMunicipalities: number;
    communities: Record<string, CommunityCoverage>;
  };
  omissions: Array<{
    ineCode: string;
    municipality: string;
    autonomousCommunity: string;
    autonomousCommunityCode: string;
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
