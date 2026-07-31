import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

const root = process.cwd();
const deployment = JSON.parse(
  readFileSync(resolve(root, "deployments/bradbury.json"), "utf8"),
);
const source = JSON.parse(
  readFileSync(resolve(root, "deployments/migration-payload.json"), "utf8"),
);
const client = createClient({ chain: testnetBradbury });
const getters = [
  ["get_stations", "stations"],
  ["get_sensors", "sensors"],
  ["get_signals", "signals"],
  ["get_incidents", "incidents"],
  ["get_inspections", "inspections"],
];
const result = {};
for (const [getter, key] of getters) {
  const records = await client.readContract({
    address: deployment.contractAddress,
    functionName: getter,
    args: [],
    jsonSafeReturn: true,
  });
  assert.deepEqual(records, source[key], `${key} did not migrate exactly`);
  result[getter] = records;
}
const overview = await client.readContract({
  address: deployment.contractAddress,
  functionName: "get_overview",
  args: [],
  jsonSafeReturn: true,
});
for (const [key, value] of Object.entries(source.overview)) {
  assert.equal(overview[key], value, `overview.${key} does not match`);
}
assert.equal(overview.migration_source_network, "StudioNet");
assert.equal(
  overview.migration_source_contract.toLowerCase(),
  source.source.contract.toLowerCase(),
);
assert.equal(
  overview.migration_source_transactions,
  source.source.accepted_transactions,
);
assert.equal(overview.migration_snapshot_hash, deployment.migration.snapshotHash);
assert.equal(overview.migration_complete, true);
result.get_overview = overview;
const verification = {
  verifiedAt: new Date().toISOString(),
  network: "Bradbury",
  contractAddress: deployment.contractAddress,
  migrationTransaction: deployment.migration.transactionHash,
  exactStateMatch: true,
  state: result,
};
writeFileSync(
  resolve(root, "deployments/live-state-bradbury.json"),
  `${JSON.stringify(verification, null, 2)}\n`,
);
console.log(JSON.stringify({ ...verification, state: undefined }, null, 2));
