import assert from "node:assert/strict";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const root = process.cwd();
const deployment = JSON.parse(readFileSync(resolve(root, "deployments/studionet.json"), "utf8"));
const client = createClient({ chain: studionet });
const read = (functionName, args = []) => client.readContract({
  address: deployment.contractAddress,
  functionName,
  args,
  jsonSafeReturn: true,
});

const [overview, stations, sensors, signals, incidents, inspections] = await Promise.all([
  read("get_overview"),
  read("get_stations"),
  read("get_sensors"),
  read("get_signals"),
  read("get_incidents"),
  read("get_inspections"),
]);
assert.equal(stations.length, 6);
assert.equal(sensors.length, 8);
assert.ok(signals.length >= 3);
assert.ok(incidents.length >= 1);
assert.ok(inspections.length >= 1);
assert.ok(signals.filter((item) => item.status === "RESOLVED").every((item) => item.evidence_verified));
assert.ok(signals.filter((item) => item.status === "RESOLVED").every((item) => item.evidence_digest.length === 64));
assert.ok(incidents.every((item) => item.response_code && item.response));
assert.ok(inspections.filter((item) => item.status === "RESOLVED").every((item) => item.evidence_verified));
assert.ok(inspections.filter((item) => item.status === "RESOLVED").every((item) => item.response_assessment));

const output = {
  verifiedAt: new Date().toISOString(),
  network: "StudioNet",
  contractAddress: deployment.contractAddress,
  overview,
  counts: {
    stations: stations.length,
    sensors: sensors.length,
    signals: signals.length,
    incidents: incidents.length,
    inspections: inspections.length,
  },
  evidenceVerified: true,
  requiredResponseRecorded: true,
};
writeFileSync(
  resolve(root, "deployments/live-state-studionet.json"),
  `${JSON.stringify(output, null, 2)}\n`,
);
console.log(JSON.stringify(output, null, 2));
