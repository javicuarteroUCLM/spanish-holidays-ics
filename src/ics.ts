import { createHash } from "node:crypto";
import ICAL from "ical.js";
import type { Holiday, Municipality, SourceManifest } from "./model.js";

function compactDate(value: string): string {
  return value.replaceAll("-", "");
}

function nextDate(value: string): string {
  const date = new Date(`${value}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString().slice(0, 10);
}

function escapeText(value: string): string {
  return value
    .replaceAll("\\", "\\\\")
    .replaceAll(/\r\n|\r|\n/g, "\\n")
    .replaceAll(",", "\\,")
    .replaceAll(";", "\\;");
}

export function foldLine(line: string): string[] {
  const lines: string[] = [];
  let current = "";
  let currentBytes = 0;
  let capacity = 75;
  for (const character of line) {
    const bytes = Buffer.byteLength(character, "utf8");
    if (currentBytes + bytes > capacity && current.length > 0) {
      lines.push(current);
      current = " ";
      currentBytes = 1;
      capacity = 75;
    }
    current += character;
    currentBytes += bytes;
  }
  lines.push(current);
  return lines;
}

function stableEventUid(
  municipality: Municipality,
  date: string,
  holidays: Holiday[],
): string {
  const sourceIdentity = holidays
    .map(
      (holiday) =>
        `${holiday.scope}:${holiday.provenance.sourceId}:${holiday.provenance.sourceRecordId}`,
    )
    .sort()
    .join("|");
  const digest = createHash("sha256")
    .update(
      `${holidayYear(holidays)}:${municipality.ineCode}:${date}:${sourceIdentity}`,
    )
    .digest("hex");
  return `${digest}@spanish-holidays-ics`;
}

function holidayYear(holidays: Holiday[]): number {
  const years = new Set(holidays.map((holiday) => holiday.year));
  if (years.size !== 1)
    throw new Error("A calendar event cannot combine different years");
  return holidays[0]?.year ?? 0;
}

function deterministicTimestamp(manifest: SourceManifest): string {
  return new Date(manifest.retrievedAt)
    .toISOString()
    .replaceAll(/[-:]/g, "")
    .replace(".000", "");
}

export function serializeCalendar(
  municipality: Municipality,
  holidays: Holiday[],
  manifest: SourceManifest,
): string {
  const byDate = new Map<string, Holiday[]>();
  for (const holiday of holidays) {
    byDate.set(holiday.date, [...(byDate.get(holiday.date) ?? []), holiday]);
  }

  const contentLines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "PRODID:-//spanish-holidays-ics//Municipal Holidays 2026//EN",
    `X-WR-CALNAME:${escapeText(`Public holidays 2026 - ${municipality.name}`)}`,
  ];
  for (const [date, dateHolidays] of [...byDate.entries()].sort(
    ([left], [right]) => left.localeCompare(right),
  )) {
    const ordered = [...dateHolidays].sort((left, right) =>
      `${left.scope}:${left.name}`.localeCompare(
        `${right.scope}:${right.name}`,
      ),
    );
    const summary = [...new Set(ordered.map((holiday) => holiday.name))].join(
      " / ",
    );
    const provenance = ordered
      .map(
        (holiday) =>
          `${holiday.scope}: ${holiday.provenance.sourceId}/${holiday.provenance.sourceRecordId}`,
      )
      .join("; ");
    contentLines.push(
      "BEGIN:VEVENT",
      `UID:${stableEventUid(municipality, date, ordered)}`,
      `DTSTAMP:${deterministicTimestamp(manifest)}`,
      `DTSTART;VALUE=DATE:${compactDate(date)}`,
      `DTEND;VALUE=DATE:${compactDate(nextDate(date))}`,
      `SUMMARY:${escapeText(summary)}`,
      `DESCRIPTION:${escapeText(`Source provenance - ${provenance}`)}`,
      "TRANSP:TRANSPARENT",
      "CATEGORIES:PUBLIC HOLIDAY",
      "END:VEVENT",
    );
  }
  contentLines.push("END:VCALENDAR");
  return `${contentLines.flatMap(foldLine).join("\r\n")}\r\n`;
}

export function assertStructurallyValidIcs(ics: string): void {
  if (!ics.endsWith("\r\n") || /(^|[^\r])\n/.test(ics)) {
    throw new Error("ICS must use CRLF line endings and end with CRLF");
  }
  const physicalLines = ics.slice(0, -2).split("\r\n");
  for (const line of physicalLines) {
    if (Buffer.byteLength(line, "utf8") > 75) {
      throw new Error(`ICS content line exceeds 75 octets: ${line}`);
    }
  }
  if (
    physicalLines[0] !== "BEGIN:VCALENDAR" ||
    physicalLines.at(-1) !== "END:VCALENDAR"
  ) {
    throw new Error("ICS is missing its VCALENDAR envelope");
  }
  const starts = physicalLines.filter((line) => line === "BEGIN:VEVENT").length;
  const ends = physicalLines.filter((line) => line === "END:VEVENT").length;
  if (starts === 0 || starts !== ends)
    throw new Error("ICS has unbalanced VEVENT components");

  try {
    // ical.js intentionally exposes its parse tree as `any`; constructing a
    // component is the library's documented parse boundary.
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    new ICAL.Component(ICAL.parse(ics));
  } catch (error) {
    throw new Error("ICS cannot be parsed as RFC 5545", { cause: error });
  }
}
