import { describe, expect, it } from "vitest";
import { assertIneCode, assertIsoDate } from "../src/model.js";

describe("canonical value validation", () => {
  it("accepts only real ISO dates in the target year", () => {
    expect(() => assertIsoDate("2026-02-28")).not.toThrow();
    expect(() => assertIsoDate("2026-02-30")).toThrow("Invalid calendar date");
    expect(() => assertIsoDate("2025-12-25")).toThrow("2026");
  });

  it("accepts only five-digit INE municipality codes", () => {
    expect(() => assertIneCode("04001")).not.toThrow();
    expect(() => assertIneCode("4001")).toThrow("five-digit INE");
    expect(() => assertIneCode("04A01")).toThrow("five-digit INE");
  });
});
