import { createHash } from "node:crypto";
import ICAL from "ical.js";
import { describe, expect, it } from "vitest";
import {
  assertStructurallyValidIcs,
  foldLine,
  serializeCalendar,
} from "../src/ics.js";
import type { Holiday, Municipality, SourceManifest } from "../src/model.js";

const municipality: Municipality = {
  ineCode: "04001",
  controlDigit: "0",
  name: "Árbol de la prueba",
  provinceCode: "04",
  autonomousCommunityCode: "01",
};
const manifest: SourceManifest = {
  schemaVersion: 1,
  year: 2026,
  retrievedAt: "2026-09-06T11:54:28Z",
  sources: [],
};
const holiday: Holiday = {
  year: 2026,
  date: "2026-05-01",
  name: "Fiesta, trabajo; y árbol con un nombre deliberadamente largo para plegar",
  scope: "country",
  jurisdictionCode: "ES",
  provenance: {
    sourceId: "official-source",
    sourceRecordId: "record-1",
    sourceUrl: "https://example.invalid/source",
  },
};

describe("RFC 5545 serialization", () => {
  it("folds UTF-8 content lines at no more than 75 octets", () => {
    const folded = foldLine(`SUMMARY:${"á".repeat(50)}`);
    expect(folded.length).toBeGreaterThan(1);
    expect(folded.slice(1).every((line) => line.startsWith(" "))).toBe(true);
    expect(folded.every((line) => Buffer.byteLength(line, "utf8") <= 75)).toBe(
      true,
    );
  });

  it("creates a deterministic, parseable all-day event with an exclusive end", () => {
    const first = serializeCalendar(municipality, [holiday], manifest);
    const second = serializeCalendar(municipality, [holiday], manifest);
    expect(first).toBe(second);
    expect(first).toContain("DTSTAMP:20260906T115428Z\r\n");
    expect(first).toContain("DTSTART;VALUE=DATE:20260501\r\n");
    expect(first).toContain("DTEND;VALUE=DATE:20260502\r\n");
    expect(first).toContain("Fiesta\\, trabajo\\; y árbol");
    assertStructurallyValidIcs(first);

    // ical.js intentionally exposes its parse tree as `any`; constructing a
    // component is the library's documented validation boundary.
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    const component = new ICAL.Component(ICAL.parse(first));
    const events = component.getAllSubcomponents("vevent");
    expect(events).toHaveLength(1);
    expect(String(events[0]?.getFirstPropertyValue("dtstart"))).toBe(
      "2026-05-01",
    );
    expect(String(events[0]?.getFirstPropertyValue("dtend"))).toBe(
      "2026-05-02",
    );
  });

  it("preserves every source identity when same-date holidays are deduplicated", () => {
    const local = {
      ...holiday,
      name: "FIESTA LOCAL EN ÁRBOL DE LA PRUEBA",
      scope: "municipality" as const,
      jurisdictionCode: municipality.ineCode,
      provenance: {
        ...holiday.provenance,
        sourceId: "local-source",
        sourceRecordId: "42",
      },
    };
    const content = serializeCalendar(municipality, [holiday, local], manifest);
    expect(content.match(/BEGIN:VEVENT/g)).toHaveLength(1);
    expect(content).toContain("official-source/record-1");
    expect(content).toContain("local-source/42");
    const unfolded = content.replaceAll("\r\n ", "");
    const uid = unfolded.match(/UID:([^\r]+)/)?.[1];
    expect(uid).toBe(
      `${createHash("sha256")
        .update(
          "2026:04001:2026-05-01:country:official-source:record-1|municipality:local-source:42",
        )
        .digest("hex")}@spanish-holidays-ics`,
    );
  });

  it("rejects malformed line endings", () => {
    expect(() =>
      assertStructurallyValidIcs("BEGIN:VCALENDAR\nEND:VCALENDAR\n"),
    ).toThrow("CRLF");
  });
});
