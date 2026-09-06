#!/usr/bin/env node
import { assertDeterministic, generate, validate } from "./pipeline.js";

const command = process.argv[2];

try {
  if (command === "generate") {
    const index = await generate();
    console.log(
      `Generated ${index.summary.completeCalendars} complete calendars; omitted ${index.summary.omittedMunicipalities} municipalities.`,
    );
  } else if (command === "validate") {
    const index = await validate();
    await assertDeterministic();
    console.log(
      `Validated ${index.summary.completeCalendars} calendars and deterministic regeneration.`,
    );
  } else {
    throw new Error("Usage: node dist/cli.js <generate|validate>");
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
