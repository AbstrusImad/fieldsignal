import { readFileSync, writeFileSync } from "node:fs";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const deployment = JSON.parse(readFileSync("deployments/studionet.json", "utf8"));
const seed = JSON.parse(readFileSync("deployments/seed-studionet.json", "utf8"));
const client = createClient({ chain: studionet });
const methods = [
  "get_overview",
  "get_stations",
  "get_sensors",
  "get_signals",
  "get_incidents",
  "get_inspections",
];
const state = {};

for (const functionName of methods) {
  state[functionName] = await client.readContract({
    address: deployment.contractAddress,
    functionName,
    args: [],
    jsonSafeReturn: true,
  });
}

const output = {
  verifiedAt: new Date().toISOString(),
  network: "StudioNet",
  contractAddress: deployment.contractAddress,
  deploymentTransaction: deployment.transactionHash,
  acceptedActivityTransactions: seed.transactions.filter(
    (transaction) => transaction.succeeded,
  ).length,
  state,
};
writeFileSync(
  "deployments/live-state-studionet.json",
  `${JSON.stringify(output, null, 2)}\n`,
);
console.log(JSON.stringify(output, null, 2));
