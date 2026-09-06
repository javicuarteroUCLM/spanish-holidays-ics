import { cp, mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import ICAL from "ical.js";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import {
  loadAndaluciaLocalHolidays,
  loadAndVerifyManifest,
  loadBoeHolidays,
  loadMunicipalities,
  loadNameMap,
} from "../src/adapters.js";
import { assertDeterministic, generate, validate } from "../src/pipeline.js";

let fixtureRoot: string;

beforeAll(async () => {
  fixtureRoot = await mkdtemp(path.join(tmpdir(), "spanish-holidays-ics-"));
  await cp(path.resolve("data"), path.join(fixtureRoot, "data"), {
    recursive: true,
  });
  await generate(fixtureRoot);
});

afterAll(async () => {
  await rm(fixtureRoot, { recursive: true, force: true });
});

describe("official-source adapters", () => {
  it("verifies checksums and complete Andalucía joins", async () => {
    const manifest = await loadAndVerifyManifest(fixtureRoot);
    const municipalities = await loadMunicipalities(fixtureRoot, manifest);
    const nameMap = await loadNameMap(fixtureRoot, manifest);
    const common = await loadBoeHolidays(fixtureRoot, manifest);
    const local = await loadAndaluciaLocalHolidays(
      fixtureRoot,
      manifest,
      nameMap,
    );

    expect(municipalities).toHaveLength(785);
    expect(nameMap.mappings).toHaveLength(774);
    expect(nameMap.omitted).toHaveLength(11);
    expect(
      nameMap.mappings.filter((mapping) => mapping.method === "manual-alias"),
    ).toHaveLength(9);
    expect(common).toHaveLength(12);
    expect(local).toHaveLength(1548);
  });
});

describe("production generation", () => {
  it("generates only complete calendars and declares every omission", async () => {
    const index = await generate(fixtureRoot);
    expect(index.status).toBe("partial-andalucia-coverage");
    expect(index.summary).toEqual({
      totalAndaluciaMunicipalities: 785,
      completeCalendars: 774,
      omittedMunicipalities: 11,
    });
    expect(index.omissions).toHaveLength(11);
    expect(index.calendars.every((calendar) => calendar.complete)).toBe(true);
    expect(
      index.calendars.every((calendar) => calendar.localHolidayCount === 2),
    ).toBe(true);
    expect(
      index.calendars.every((calendar) =>
        calendar.path.startsWith("2026/andalucia/"),
      ),
    ).toBe(true);
    expect(await readdir(path.join(fixtureRoot, "calendars/2026"))).toEqual([
      "andalucia",
    ]);
    expect(
      await readdir(path.join(fixtureRoot, "calendars/2026/andalucia")),
    ).toHaveLength(774);
    expect(
      await readFile(
        path.join(fixtureRoot, "calendars/2026/andalucia/04001-abla.ics"),
        "utf8",
      ),
    ).toBe(
      await readFile(path.resolve("tests/fixtures/04001-abla.ics"), "utf8"),
    );
  });

  it("produces files parseable by ical.js with date-only events", async () => {
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
  });

  it("rebuilds byte-for-byte deterministically", async () => {
    await expect(assertDeterministic(fixtureRoot)).resolves.toBeUndefined();
  });
});
