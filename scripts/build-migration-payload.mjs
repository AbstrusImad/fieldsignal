import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = process.cwd();
const source = JSON.parse(
  readFileSync(resolve(root, "deployments/live-state-studionet.json"), "utf8"),
);
const state = source.state;
const migration = {
  source: {
    network: "StudioNet",
    contract: source.contractAddress,
    accepted_transactions: source.acceptedActivityTransactions,
    verified_at: source.verifiedAt,
  },
  overview: state.get_overview,
  stations: state.get_stations,
  sensors: state.get_sensors,
  signals: state.get_signals,
  incidents: state.get_incidents,
  inspections: state.get_inspections,
};
const payload = JSON.stringify(migration);
const snapshotHash = createHash("sha256").update(payload).digest("hex");
const counts = Object.fromEntries(
  ["stations", "sensors", "signals", "incidents", "inspections"].map((key) => [
    key,
    migration[key].length,
  ]),
);
const manifest = {
  snapshotHash,
  payloadBytes: Buffer.byteLength(payload),
  migratedRecords: Object.values(counts).reduce((total, count) => total + count, 0),
  counts,
  source: migration.source,
};

writeFileSync(
  resolve(root, "deployments/migration-payload.json"),
  `${JSON.stringify(migration, null, 2)}\n`,
);
writeFileSync(
  resolve(root, "deployments/migration-manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
);
console.log(JSON.stringify(manifest, null, 2));
