import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  loadAndVerifyManifest,
  loadBoeHolidays,
  loadCommunityList,
  loadLocalHolidays,
  loadMunicipalities,
  type LoadedLocalHolidays,
} from "./adapters.js";
import { assertStructurallyValidIcs, serializeCalendar } from "./ics.js";
import {
  TARGET_YEAR,
  communityByCode,
  type CalendarIndexEntry,
  type CommunityCoverage,
  type CommunityDefinition,
  type CoverageIndex,
  type Holiday,
  type Municipality,
} from "./model.js";

const CALENDARS_ROOT = "calendars";
const INDEX_FILENAME = "index.json";

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

function calendarDirectory(
  root: string,
  community: CommunityDefinition,
): string {
  return path.join(root, CALENDARS_ROOT, String(TARGET_YEAR), community.slug);
}

interface CommunityPlan {
  community: CommunityDefinition;
  loaded: LoadedLocalHolidays;
  roster: Municipality[];
  municipalityByCode: Map<string, Municipality>;
}

function countryHolidays(holidays: Holiday[]): Holiday[] {
  const byDate = new Map<string, Holiday>();
  for (const holiday of holidays) {
    if (holiday.scope !== "country") continue;
    byDate.set(holiday.date, holiday);
  }
  return [...byDate.values()];
}

function communityHolidays(holidays: Holiday[], code: string): Holiday[] {
  return holidays.filter(
    (holiday) =>
      holiday.scope === "autonomous-community" &&
      holiday.jurisdictionCode === code,
  );
}

function calendarHolidays(
  municipality: Municipality,
  plan: CommunityPlan,
  common: Holiday[],
): Holiday[] {
  const model = plan.community.localModel;
  const holidays: Holiday[] = [];
  const local = plan.loaded.municipalities.get(municipality.ineCode);
  if (local === undefined) {
    throw new Error(
      `Cannot advertise incomplete calendar for ${municipality.ineCode}`,
    );
  }
  holidays.push(...countryHolidays(common));
  holidays.push(...communityHolidays(common, plan.community.code));
  if (model === "two-local-plus-island") {
    for (const island of plan.loaded.file.islandDays ?? []) {
      if (island.ineCodes.includes(municipality.ineCode)) {
        holidays.push({
          year: TARGET_YEAR,
          date: island.date,
          name: island.feast,
          scope: "island",
          jurisdictionCode: island.island,
          provenance: {
            sourceId: "boc-decreto-61-2025",
            sourceRecordId: `island:${island.island}`,
            sourceUrl:
              "https://www.gobiernodecanarias.org/boc/2025/088/1659.html",
          },
        });
      }
    }
  }
  if (model === "one-local-plus-province") {
    for (const day of plan.loaded.file.provinceDays ?? []) {
      if (day.provinceCode === municipality.provinceCode) {
        holidays.push({
          year: TARGET_YEAR,
          date: day.date,
          name: day.name,
          scope: "province",
          jurisdictionCode: day.provinceCode,
          provenance: {
            sourceId: "euskadi-calendario-laboral-2026",
            sourceRecordId: day.sourceRecordId,
            sourceUrl:
              "https://opendata.euskadi.eus/catalogo/-/calendario-laboral-de-euskadi-para-el-2026/",
          },
        });
      }
    }
  }
  if (model === "one-plus-shared") {
    const shared = plan.loaded.file.sharedLocalDay;
    if (shared === undefined) {
      throw new Error(`Navarra file is missing its shared local day`);
    }
    holidays.push({
      year: TARGET_YEAR,
      date: shared.date,
      name: shared.name,
      scope: "municipality",
      jurisdictionCode: municipality.ineCode,
      provenance: {
        sourceId: "bon-241-2025",
        sourceRecordId: shared.sourceRecordId,
        sourceUrl: "https://bon.navarra.es/es/anuncio/-/texto/2025/241/12",
      },
    });
  }
  for (const datum of local.holidays) {
    holidays.push({
      year: TARGET_YEAR,
      date: datum.date,
      name: datum.name,
      scope: "municipality",
      jurisdictionCode: municipality.ineCode,
      provenance: {
        sourceId: plan.loaded.file.sources[0]?.sourceId ?? "local",
        sourceRecordId: datum.sourceRecordId,
        sourceUrl: "",
      },
    });
  }
  return holidays;
}

function buildCommunityPlans(
  municipalities: Municipality[],
  communities: CommunityDefinition[],
  loaded: Map<string, LoadedLocalHolidays>,
): Map<string, CommunityPlan> {
  const byCommunity = new Map<string, Municipality[]>();
  for (const municipality of municipalities) {
    const list = byCommunity.get(municipality.autonomousCommunityCode) ?? [];
    list.push(municipality);
    byCommunity.set(municipality.autonomousCommunityCode, list);
  }
  const plans = new Map<string, CommunityPlan>();
  for (const community of communities) {
    const plan: CommunityPlan = {
      community,
      loaded: loaded.get(community.code) ?? loadEmpty(community),
      roster: byCommunity.get(community.code) ?? [],
      municipalityByCode: new Map(
        (byCommunity.get(community.code) ?? []).map((municipality) => [
          municipality.ineCode,
          municipality,
        ]),
      ),
    };
    plans.set(community.code, plan);
  }
  return plans;
}

function loadEmpty(community: CommunityDefinition): LoadedLocalHolidays {
  return {
    file: {
      schemaVersion: 1,
      year: TARGET_YEAR,
      autonomousCommunityCode: community.code,
      autonomousCommunity: community.name,
      localHolidayModel: community.localModel,
      sources: [],
      municipalities: [],
      omissions: [],
    },
    municipalities: new Map(),
  };
}

export async function generate(root = process.cwd()): Promise<CoverageIndex> {
  const manifest = await loadAndVerifyManifest(root);
  const municipalities = await loadMunicipalities(root, manifest);
  const common = await loadBoeHolidays(root, manifest);

  const communities = loadCommunityList();
  const loaded = new Map<string, LoadedLocalHolidays>();
  for (const community of communities) {
    loaded.set(
      community.code,
      await loadLocalHolidays(root, manifest, community),
    );
  }
  const plans = buildCommunityPlans(municipalities, communities, loaded);

  // Partition every roster into covered / omitted and validate the local file.
  const omittedByCommunity = new Map<
    string,
    Array<{ ineCode: string; name: string; reason: string }>
  >();
  for (const plan of plans.values()) {
    const covered = new Set(plan.loaded.municipalities.keys());
    const rosterCodes = new Set(
      plan.roster.map((municipality) => municipality.ineCode),
    );
    const unexpectedCovered = [...covered].filter(
      (code) => !rosterCodes.has(code),
    );
    if (unexpectedCovered.length > 0) {
      throw new Error(
        `Community ${plan.community.slug} covers unknown codes: ${unexpectedCovered.join(", ")}`,
      );
    }
    const omittedCodes = new Set(
      plan.loaded.file.omissions.map((o) => o.ineCode),
    );
    const expectedOmitted = [...rosterCodes].filter(
      (code) => !covered.has(code),
    );
    const unexpectedOmitted = [...omittedCodes].filter(
      (code) => !rosterCodes.has(code),
    );
    const missingFromOmissions = expectedOmitted.filter(
      (code) => !omittedCodes.has(code),
    );
    if (unexpectedOmitted.length > 0 || missingFromOmissions.length > 0) {
      throw new Error(
        `Community ${plan.community.slug} omissions do not partition the roster: ` +
          `unexpected ${unexpectedOmitted.join(", ")}, missing ${missingFromOmissions.join(", ")}`,
      );
    }
    omittedByCommunity.set(
      plan.community.code,
      plan.loaded.file.omissions.map((o) => ({
        ineCode: o.ineCode,
        name: plan.municipalityByCode.get(o.ineCode)?.name ?? o.name,
        reason: o.reason,
      })),
    );
  }

  for (const plan of plans.values()) {
    if (plan.roster.length === 0) continue;
    const directory = calendarDirectory(root, plan.community);
    await rm(directory, { recursive: true, force: true });
    await mkdir(directory, { recursive: true });
  }

  const calendars: CalendarIndexEntry[] = [];
  for (const plan of plans.values()) {
    for (const local of plan.loaded.file.municipalities) {
      const municipality = plan.municipalityByCode.get(local.ineCode);
      if (municipality === undefined) {
        throw new Error(`Unknown mapped INE code: ${local.ineCode}`);
      }
      const holidays = calendarHolidays(municipality, plan, common);
      const ics = serializeCalendar(municipality, holidays, manifest);
      assertStructurallyValidIcs(ics);
      const filename = `${local.ineCode}-${slugify(municipality.name)}.ics`;
      await writeFile(
        path.join(calendarDirectory(root, plan.community), filename),
        ics,
        "utf8",
      );
      const localHolidayCount = holidays.filter(
        (holiday) => holiday.scope === "municipality",
      ).length;
      calendars.push({
        ineCode: local.ineCode,
        municipality: municipality.name,
        provinceCode: municipality.provinceCode,
        autonomousCommunityCode: plan.community.code,
        autonomousCommunity: plan.community.name,
        path: `${TARGET_YEAR}/${plan.community.slug}/${filename}`,
        holidayCount: new Set(holidays.map((holiday) => holiday.date)).size,
        localHolidayCount,
        complete: true,
        sha256: sha256(ics),
      });
    }
  }

  const communityCoverage: Record<string, CommunityCoverage> = {};
  for (const plan of plans.values()) {
    const total = plan.roster.length;
    const complete = plan.loaded.file.municipalities.length;
    communityCoverage[plan.community.slug] = {
      total,
      complete,
      omitted: total - complete,
    };
  }
  const totalOmitted = [...omittedByCommunity.values()].reduce(
    (sum, list) => sum + list.length,
    0,
  );

  const index: CoverageIndex = {
    schemaVersion: 2,
    year: TARGET_YEAR,
    generatedAt: manifest.retrievedAt,
    status: "national-partial-coverage",
    scope: "España",
    summary: {
      totalMunicipalities: municipalities.length,
      completeCalendars: calendars.length,
      omittedMunicipalities: totalOmitted,
      communities: communityCoverage,
    },
    omissions: [...omittedByCommunity.values()]
      .flat()
      .sort((left, right) => left.ineCode.localeCompare(right.ineCode))
      .map((omission) => {
        const municipality = municipalities.find(
          (item) => item.ineCode === omission.ineCode,
        );
        const community = communityByCode(
          municipality?.autonomousCommunityCode ?? "",
        );
        return {
          ineCode: omission.ineCode,
          municipality: omission.name,
          autonomousCommunity: community.name,
          autonomousCommunityCode: community.code,
          reason: omission.reason,
        };
      }),
    calendars: calendars.sort((left, right) =>
      left.ineCode.localeCompare(right.ineCode),
    ),
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
  const communities = loadCommunityList();
  const loaded = new Map<string, LoadedLocalHolidays>();
  for (const community of communities) {
    loaded.set(
      community.code,
      await loadLocalHolidays(root, manifest, community),
    );
  }
  const plans = buildCommunityPlans(municipalities, communities, loaded);

  const parsed = JSON.parse(
    await readFile(path.join(root, CALENDARS_ROOT, INDEX_FILENAME), "utf8"),
  ) as CoverageIndex;
  if (
    parsed.year !== TARGET_YEAR ||
    parsed.summary.totalMunicipalities !== municipalities.length
  ) {
    throw new Error("Coverage index does not match the national roster");
  }
  let expectedComplete = 0;
  let expectedOmitted = 0;
  for (const plan of plans.values()) {
    expectedComplete += plan.loaded.file.municipalities.length;
    expectedOmitted += plan.loaded.file.omissions.length;
    if (plan.community.slug === "canarias") {
      const directory = calendarDirectory(root, plan.community);
      const islandCount = plan.loaded.file.islandDays?.length ?? 0;
      if (islandCount !== 7) {
        throw new Error("Canarias island-day count must be 7");
      }
      void directory;
    }
  }
  if (
    parsed.summary.completeCalendars !== expectedComplete ||
    parsed.summary.omittedMunicipalities !== expectedOmitted ||
    parsed.calendars.length !== expectedComplete
  ) {
    throw new Error("Coverage index summary does not match normalized sources");
  }
  for (const plan of plans.values()) {
    if (plan.roster.length === 0) continue;
    const directory = calendarDirectory(root, plan.community);
    const outputFiles = (await readdir(directory)).filter((file) =>
      file.endsWith(".ics"),
    );
    const expectedFiles = plan.loaded.file.municipalities.map(
      (local) =>
        `${local.ineCode}-${slugify(plan.municipalityByCode.get(local.ineCode)?.name ?? "")}.ics`,
    );
    if (outputFiles.length !== expectedFiles.length) {
      throw new Error(
        `Community ${plan.community.slug}: expected ${expectedFiles.length} ICS files, found ${outputFiles.length}`,
      );
    }
    for (const filename of expectedFiles) {
      if (!outputFiles.includes(filename)) {
        throw new Error(
          `Community ${plan.community.slug}: missing ${filename}`,
        );
      }
    }
  }
  for (const calendar of parsed.calendars) {
    const absolutePath = path.join(root, CALENDARS_ROOT, calendar.path);
    const ics = await readFile(absolutePath, "utf8");
    assertStructurallyValidIcs(ics);
    if (sha256(ics) !== calendar.sha256 || !calendar.complete) {
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
