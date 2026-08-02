import fs from "node:fs";
import { simulateComparison } from "./simulation-core.mjs";

const [referencePath, overridesJson = "{}"] = process.argv.slice(2);
if (!referencePath) {
  console.error("usage: node browser/simulate-cli.mjs <reference.json> [overrides-json]");
  process.exit(2);
}
const reference = JSON.parse(fs.readFileSync(referencePath, "utf8"));
const overrides = JSON.parse(overridesJson);
const result = await simulateComparison(reference, overrides);
process.stdout.write(JSON.stringify(result));
