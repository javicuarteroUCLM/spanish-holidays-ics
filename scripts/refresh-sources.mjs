#!/usr/bin/env node
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const manifestPath = path.resolve("data/sources/2026/manifest.json");
const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const mode = process.argv[2] ?? "--check";

if (mode !== "--check" && mode !== "--write") {
  throw new Error("Usage: node scripts/refresh-sources.mjs <--check|--write>");
}

let changed = false;
for (const source of manifest.sources) {
  const response = await fetch(source.url, {
    headers: { "User-Agent": "spanish-holidays-ics source refresh" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch ${source.id}: HTTP ${response.status}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  const digest = createHash("sha256").update(bytes).digest("hex");
  const status = digest === source.sha256 ? "unchanged" : "CHANGED";
  console.log(`${source.id}: ${status} (${digest})`);
  if (digest === source.sha256) continue;
  changed = true;
  if (mode === "--write") {
    await writeFile(path.resolve(source.path), bytes);
    source.sha256 = digest;
  }
}

if (mode === "--write" && changed) {
  manifest.retrievedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  await writeFile(
    manifestPath,
    `${JSON.stringify(manifest, null, 2)}\n`,
    "utf8",
  );
  console.log("Frozen inputs and manifest updated.");
  console.log(
    "Next: run scripts/extract-ine-xlsx.py and scripts/build-andalucia-name-map.py.",
  );
  console.log(
    "Then independently audit data/normalized/2026/boe-andalucia-holidays.json against the new BOE snapshot before updating its sourceSha256.",
  );
} else if (mode === "--check" && changed) {
  process.exitCode = 2;
  console.error(
    "Official sources changed; run npm run sources:refresh in a dedicated update change.",
  );
}
