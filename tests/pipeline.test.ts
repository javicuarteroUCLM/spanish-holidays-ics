import { cp, mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import ICAL from "ical.js";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import {
  loadAndVerifyManifest,
  loadBoeHolidays,
  loadLocalHolidays,
  loadMunicipalities,
} from "../src/adapters.js";
import { assertDeterministic, generate, validate } from "../src/pipeline.js";
import { COMMUNITIES } from "../src/model.js";

// National generation writes ~7,200 ICS files; the default 5s vitest timeout
// is far too short, so every heavy hook/test carries an explicit timeout.
const HEAVY = 180_000;

let fixtureRoot: string;

beforeAll(async () => {
  fixtureRoot = await mkdtemp(path.join(tmpdir(), "spanish-holidays-ics-"));
  await cp(path.resolve("data"), path.join(fixtureRoot, "data"), {
    recursive: true,
  });
  await generate(fixtureRoot);
}, HEAVY);

afterAll(async () => {
  await rm(fixtureRoot, { recursive: true, force: true });
});

describe("official-source adapters", () => {
  it("verifies checksums and national roster", async () => {
    const manifest = await loadAndVerifyManifest(fixtureRoot);
    const municipalities = await loadMunicipalities(fixtureRoot, manifest);
    const common = await loadBoeHolidays(fixtureRoot, manifest);

    expect(municipalities).toHaveLength(8132);
    // 19 communities x 12 non-local days; the Canarias column has 11 in the
    // BOE matrix (its island day lives in the BOC decree).
    expect(common).toHaveLength(19 * 12 - 1);
    expect(manifest.sources.length).toBeGreaterThan(30);
  });

  it("loads every community local-holidays file", async () => {
    const manifest = await loadAndVerifyManifest(fixtureRoot);
    for (const community of COMMUNITIES) {
      const loaded = await loadLocalHolidays(fixtureRoot, manifest, community);
      expect(loaded.file.autonomousCommunityCode).toBe(community.code);
      expect(loaded.file.localHolidayModel).toBe(community.localModel);
      expect(loaded.file.sources.length).toBeGreaterThan(0);
    }
  });
});

describe("production generation", () => {
  it(
    "generates complete calendars for every covered community",
    async () => {
      const index = await generate(fixtureRoot);
      expect(index.schemaVersion).toBe(2);
      expect(index.status).toBe("national-partial-coverage");
      expect(index.summary.totalMunicipalities).toBe(8132);
      expect(
        index.summary.completeCalendars + index.summary.omittedMunicipalities,
      ).toBe(8132);
      expect(Object.keys(index.summary.communities).length).toBe(19);
      for (const community of COMMUNITIES) {
        const coverage = index.summary.communities[community.slug];
        expect(coverage).toBeDefined();
        expect(coverage!.total).toBeGreaterThan(0);
      }
      expect(index.calendars.every((calendar) => calendar.complete)).toBe(true);
      const directories = await readdir(
        path.join(fixtureRoot, "calendars/2026"),
      );
      expect(directories.sort()).toEqual(
        COMMUNITIES.map((community) => community.slug).sort(),
      );
    },
    HEAVY,
  );

  it(
    "produces files parseable by ical.js with date-only events",
    async () => {
      const index = await validate(fixtureRoot);
      for (const calendar of index.calendars) {
        const content = await readFile(
          path.join(fixtureRoot, "calendars", calendar.path),
          "utf8",
        );
        // ical.js intentionally exposes its parse tree as `any`; constructing a
        // component is the library's documented validation boundary.
        // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
        const component = new ICAL.Component(ICAL.parse(content));
        const events = component.getAllSubcomponents("vevent");
        expect(events).toHaveLength(calendar.holidayCount);
        for (const event of events) {
          const start = String(event.getFirstPropertyValue("dtstart"));
          const end = String(event.getFirstPropertyValue("dtend"));
          expect(start).toMatch(/^2026-\d{2}-\d{2}$/);
          const expectedEnd = new Date(`${start}T00:00:00Z`);
          expectedEnd.setUTCDate(expectedEnd.getUTCDate() + 1);
          expect(end).toBe(expectedEnd.toISOString().slice(0, 10));
        }
      }
    },
    HEAVY,
  );

  it(
    "records every omission grouped by autonomous community",
    async () => {
      const index = await generate(fixtureRoot);
      expect(index.omissions.length).toBe(index.summary.omittedMunicipalities);
      for (const omission of index.omissions) {
        expect(omission.autonomousCommunity).toBeTruthy();
        expect(omission.reason.length).toBeGreaterThan(0);
      }
      const catalunyaOmitted = new Set(
        index.omissions
          .filter((o) => o.autonomousCommunityCode === "09")
          .map((o) => o.ineCode),
      );
      expect(catalunyaOmitted.has("08031")).toBe(true); // Calaf
      expect(catalunyaOmitted.has("25030")).toBe(true); // Pont de Bar, El
    },
    HEAVY,
  );

  it(
    "rebuilds byte-for-byte deterministically",
    async () => {
      await expect(assertDeterministic(fixtureRoot)).resolves.toBeUndefined();
    },
    HEAVY,
  );

  it("keeps the published Andalucía reference calendar stable", async () => {
    // 04001 Abla (Almería) must be byte-identical to the checked-in fixture.
    const reference = await readFile(
      path.resolve("tests/fixtures/04001-abla.ics"),
      "utf8",
    );
    const generated = await readFile(
      path.join(fixtureRoot, "calendars/2026/andalucia/04001-abla.ics"),
      "utf8",
    );
    expect(generated).toBe(reference);
  });

  it(
    "applies the 2026 amendment chain to superseded local dates",
    async () => {
      // Official amendment resolutions replace base local dates; the
      // generated calendars must carry the amended date and never the
      // superseded one. Covers CV (DOGV 10281), Navarra (BON 1, Resolución
      // 765/2025) and Extremadura (DOE amendment chain through 23/07/2026).
      const index = await generate(fixtureRoot);
      const byCode = new Map(
        index.calendars.map((calendar) => [calendar.ineCode, calendar]),
      );
      const expectations: Array<{
        ineCode: string;
        municipality: string;
        mustInclude: string[];
        mustExclude: string[];
      }> = [
        // Comunitat Valenciana — DOGV 10281 (15/01/2026) over DOGV 10238.
        {
          ineCode: "03007",
          municipality: "Alcosser",
          mustInclude: ["2026-03-20"],
          mustExclude: ["2026-05-20"],
        },
        {
          ineCode: "03096",
          municipality: "Onil",
          mustInclude: ["2026-04-30"],
          mustExclude: ["2026-11-28"],
        },
        {
          ineCode: "03103",
          municipality: "Penàguila",
          mustInclude: ["2026-08-24"],
          mustExclude: ["2026-08-25"],
        },
        {
          // Villamalur: 15-09 (base) and 15-05 (old parse artifact) are
          // both superseded by the DOGV 10281 correction 24-08.
          ineCode: "12131",
          municipality: "Villamalur",
          mustInclude: ["2026-08-24"],
          mustExclude: ["2026-05-15", "2026-09-15"],
        },
        {
          ineCode: "46068",
          municipality: "Benissoda",
          mustInclude: ["2026-04-13"],
          mustExclude: ["2026-04-20"],
        },
        // Navarra — BON 1 (02/01/2026), Resolución 765/2025.
        {
          ineCode: "31023",
          municipality: "Aranguren",
          mustInclude: ["2026-06-19"],
          mustExclude: ["2026-06-08"],
        },
        {
          ineCode: "31250",
          municipality: "Bera",
          mustInclude: ["2026-08-03"],
          mustExclude: ["2026-03-03"],
        },
        {
          ineCode: "31064",
          municipality: "Cadreita",
          mustInclude: ["2026-01-19"],
          mustExclude: ["2026-01-12"],
        },
        // Extremadura — DOE amendment chain (05/02 .. 23/07/2026).
        {
          ineCode: "06044",
          municipality: "Don Benito",
          mustInclude: ["2026-09-11"],
          mustExclude: ["2026-09-07"],
        },
        {
          ineCode: "06113",
          municipality: "Ribera del Fresno",
          mustInclude: ["2026-09-14"],
          mustExclude: ["2026-09-15"],
        },
        {
          ineCode: "10010",
          municipality: "Alcuéscar",
          mustInclude: ["2026-04-06", "2026-10-05"],
          mustExclude: ["2026-04-21", "2026-10-06"],
        },
        {
          ineCode: "10041",
          municipality: "Caminomorisco",
          mustInclude: ["2026-11-06"],
          mustExclude: ["2026-11-13"],
        },
        {
          // Amended twice (DOE 64 then DOE 68); the later resolution wins
          // and the intermediate 12-05 must not surface.
          ineCode: "10068",
          municipality: "Cuacos de Yuste",
          mustInclude: ["2026-04-13", "2026-09-14"],
          mustExclude: ["2026-05-12"],
        },
        {
          ineCode: "10163",
          municipality: "Salvatierra de Santiago",
          mustInclude: ["2026-07-24"],
          mustExclude: ["2026-07-25"],
        },
      ];
      for (const expectation of expectations) {
        const calendar = byCode.get(expectation.ineCode);
        expect(
          calendar,
          `${expectation.municipality} (${expectation.ineCode}) calendar exists`,
        ).toBeDefined();
        const ics = await readFile(
          path.join(fixtureRoot, "calendars", calendar!.path),
          "utf8",
        );
        const dates = [...ics.matchAll(/DTSTART;VALUE=DATE:(\d{8})/g)].map(
          (match) =>
            `${match[1]!.slice(0, 4)}-${match[1]!.slice(4, 6)}-${match[1]!.slice(6, 8)}`,
        );
        for (const date of expectation.mustInclude) {
          expect(
            dates,
            `${expectation.municipality} must include ${date}`,
          ).toContain(date);
        }
        for (const date of expectation.mustExclude) {
          expect(
            dates,
            `${expectation.municipality} must not include superseded ${date}`,
          ).not.toContain(date);
        }
      }
    },
    HEAVY,
  );
});
