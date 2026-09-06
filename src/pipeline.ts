import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  loadAndaluciaLocalHolidays,
  loadAndVerifyManifest,
  loadBoeHolidays,
  loadMunicipalities,
  loadNameMap,
} from "./adapters.js";
import { assertStructurallyValidIcs, serializeCalendar } from "./ics.js";
import {
  ANDALUCIA_CODE,
  TARGET_YEAR,
  type CalendarIndexEntry,
  type CoverageIndex,
  type Holiday,
  type Municipality,
} from "./model.js";

// Output layout: calendars/<year>/<community-slug>/<ine-code>-<slug>.ics with
// the coverage index at calendars/index.json. Register one stable ASCII slug
// per autonomous community code; generation fails closed for any code without
// a registered slug, so a new community requires an explicit mapping instead
// of an ad-hoc directory.
const CALENDARS_ROOT = "calendars";
const INDEX_FILENAME = "index.json";
const COMMUNITY_DIRECTORY_SLUGS: Readonly<Record<string, string>> = {
  [ANDALUCIA_CODE]: "andalucia",
};
const OMISSION_REASON =
  "The frozen official Andalucía source does not contain exactly two local holiday records for this municipality.";

function slugify(value: string): string {
  return value
    .normalize("NFKD")
    .replaceAll(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "-")
    .replaceAll(/^-|-$/g, "");
}

function sha256(value: string | Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

function communityDirectorySlug(autonomousCommunityCode: string): string {
  const slug = COMMUNITY_DIRECTORY_SLUGS[autonomousCommunityCode];
  if (slug === undefined) {
    throw new Error(
      `No calendar directory slug registered for autonomous community code ${autonomousCommunityCode}`,
    );
  }
  return slug;
}

function calendarDirectory(
  root: string,
  autonomousCommunityCode: string,
): string {
  return path.join(
    root,
    CALENDARS_ROOT,
    String(TARGET_YEAR),
    communityDirectorySlug(autonomousCommunityCode),
  );
}

function calendarHolidays(
  municipality: Municipality,
  common: Holiday[],
  localByCode: Map<string, Holiday[]>,
): Holiday[] {
  const local = localByCode.get(municipality.ineCode) ?? [];
  if (local.length !== 2) {
    throw new Error(
      `Cannot advertise incomplete calendar for ${municipality.ineCode}`,
    );
  }
  return [...common, ...local];
}

export async function generate(root = process.cwd()): Promise<CoverageIndex> {
  const manifest = await loadAndVerifyManifest(root);
  const municipalities = await loadMunicipalities(root, manifest);
  const nameMap = await loadNameMap(root, manifest);
  const common = await loadBoeHolidays(root, manifest);
  const local = await loadAndaluciaLocalHolidays(root, manifest, nameMap);
  const municipalityByCode = new Map(
    municipalities.map((item) => [item.ineCode, item]),
  );
  const localByCode = new Map<string, Holiday[]>();
  for (const holiday of local) {
    localByCode.set(holiday.jurisdictionCode, [
      ...(localByCode.get(holiday.jurisdictionCode) ?? []),
      holiday,
    ]);
  }

  const coveredCodes = new Set(
    nameMap.mappings.map((mapping) => mapping.ineCode),
  );
  const omittedCodes = new Set(
    nameMap.omitted.map((municipality) => municipality.ineCode),
  );
  if (coveredCodes.size !== nameMap.mappings.length) {
    throw new Error("Audited mappings contain duplicate INE codes");
  }
  if (omittedCodes.size !== nameMap.omitted.length) {
    throw new Error("Omissions contain duplicate INE codes");
  }
  const rosterCodes = new Set(
    municipalities.map((municipality) => municipality.ineCode),
  );
  const declaredCodes = new Set([...coveredCodes, ...omittedCodes]);
  if (
    declaredCodes.size !== municipalities.length ||
    [...declaredCodes].some((ineCode) => !rosterCodes.has(ineCode)) ||
    [...rosterCodes].some((ineCode) => !declaredCodes.has(ineCode))
  ) {
    throw new Error(
      "Coverage mappings and omissions do not partition the INE roster",
    );
  }
  for (const mapping of nameMap.mappings) {
    const municipality = municipalityByCode.get(mapping.ineCode);
    if (municipality?.name !== mapping.ineName) {
      throw new Error(
        `Audited mapping does not match INE record ${mapping.ineCode}`,
      );
    }
  }

  for (const communityCode of new Set(
    municipalities.map((municipality) => municipality.autonomousCommunityCode),
  )) {
    const directory = calendarDirectory(root, communityCode);
    await rm(directory, { recursive: true, force: true });
    await mkdir(directory, { recursive: true });
  }
  const calendars: CalendarIndexEntry[] = [];
  for (const ineCode of [...coveredCodes].sort()) {
    const municipality = municipalityByCode.get(ineCode);
    if (municipality === undefined)
      throw new Error(`Unknown mapped INE code: ${ineCode}`);
    const outputDirectory = calendarDirectory(
      root,
      municipality.autonomousCommunityCode,
    );
    const holidays = calendarHolidays(municipality, common, localByCode);
    const ics = serializeCalendar(municipality, holidays, manifest);
    assertStructurallyValidIcs(ics);
    const filename = `${ineCode}-${slugify(municipality.name)}.ics`;
    await writeFile(path.join(outputDirectory, filename), ics, "utf8");
    calendars.push({
      ineCode,
      municipality: municipality.name,
      provinceCode: municipality.provinceCode,
      path: `${TARGET_YEAR}/${communityDirectorySlug(
        municipality.autonomousCommunityCode,
      )}/${filename}`,
      holidayCount: new Set(holidays.map((holiday) => holiday.date)).size,
      localHolidayCount: 2,
      complete: true,
      sha256: sha256(ics),
    });
  }

  const index: CoverageIndex = {
    schemaVersion: 1,
    year: TARGET_YEAR,
    generatedAt: manifest.retrievedAt,
    status: "partial-andalucia-coverage",
    scope: "Andalucía",
    summary: {
      totalAndaluciaMunicipalities: municipalities.length,
      completeCalendars: calendars.length,
      omittedMunicipalities: nameMap.omitted.length,
    },
    omissions: [...nameMap.omitted]
      .sort((left, right) => left.ineCode.localeCompare(right.ineCode))
      .map((municipality) => ({
        ineCode: municipality.ineCode,
        municipality: municipality.name,
        reason: OMISSION_REASON,
      })),
    calendars,
    sources: manifest.sources.map(
      ({ id, authority, url, license, licenseUrl, sha256: sourceSha256 }) => ({
        id,
        authority,
        url,
        license,
        licenseUrl,
        sha256: sourceSha256,
      }),
    ),
    disclaimer:
      "This is a derived, non-official dataset. Verify critical dates against the cited official publications.",
  };
  await writeFile(
    path.join(root, CALENDARS_ROOT, INDEX_FILENAME),
    `${JSON.stringify(index, null, 2)}\n`,
    "utf8",
  );
  return index;
}

export async function validate(root = process.cwd()): Promise<CoverageIndex> {
  const manifest = await loadAndVerifyManifest(root);
  const municipalities = await loadMunicipalities(root, manifest);
  const nameMap = await loadNameMap(root, manifest);
  const common = await loadBoeHolidays(root, manifest);
  const local = await loadAndaluciaLocalHolidays(root, manifest, nameMap);
  if (common.length !== 12 || local.length !== nameMap.mappings.length * 2) {
    throw new Error("Unexpected common or local holiday count");
  }

  const parsed = JSON.parse(
    await readFile(path.join(root, CALENDARS_ROOT, INDEX_FILENAME), "utf8"),
  ) as CoverageIndex;
  if (
    parsed.year !== TARGET_YEAR ||
    parsed.summary.totalAndaluciaMunicipalities !== municipalities.length ||
    parsed.summary.completeCalendars !== nameMap.mappings.length ||
    parsed.summary.omittedMunicipalities !== nameMap.omitted.length ||
    parsed.calendars.length !== nameMap.mappings.length
  ) {
    throw new Error("Coverage index summary does not match normalized sources");
  }
  const firstMunicipality = municipalities[0];
  if (firstMunicipality === undefined) {
    throw new Error("Municipality roster is empty");
  }
  const outputDirectory = calendarDirectory(
    root,
    firstMunicipality.autonomousCommunityCode,
  );
  const outputFiles = (await readdir(outputDirectory)).filter((file) =>
    file.endsWith(".ics"),
  );
  if (outputFiles.length !== parsed.calendars.length) {
    throw new Error(
      `Expected ${parsed.calendars.length} ICS files, found ${outputFiles.length}`,
    );
  }
  for (const calendar of parsed.calendars) {
    const absolutePath = path.join(root, CALENDARS_ROOT, calendar.path);
    const ics = await readFile(absolutePath, "utf8");
    assertStructurallyValidIcs(ics);
    if (
      sha256(ics) !== calendar.sha256 ||
      calendar.localHolidayCount !== 2 ||
      !calendar.complete
    ) {
      throw new Error(`Calendar index mismatch for ${calendar.ineCode}`);
    }
  }
  return parsed;
}

export async function assertDeterministic(root = process.cwd()): Promise<void> {
  const calendarsRoot = path.join(root, CALENDARS_ROOT);
  await generate(root);
  const firstSnapshot = await snapshotTree(calendarsRoot);
  await generate(root);
  const secondSnapshot = await snapshotTree(calendarsRoot);
  if (firstSnapshot !== secondSnapshot) {
    throw new Error("Generation is not deterministic");
  }
}

async function snapshotTree(directory: string): Promise<string> {
  const entries = (await readdir(directory, { withFileTypes: true })).sort(
    (left, right) => left.name.localeCompare(right.name),
  );
  const hash = createHash("sha256");
  for (const entry of entries) {
    hash.update(entry.name);
    const absolutePath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      hash.update(await snapshotTree(absolutePath));
    } else {
      hash.update(await readFile(absolutePath));
    }
  }
  return hash.digest("hex");
}
