import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createAccount, createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

const root = process.cwd();
const deploymentPath = resolve(root, "deployments/bradbury.json");
const deployment = JSON.parse(readFileSync(deploymentPath, "utf8"));
const migration = JSON.parse(
  readFileSync(resolve(root, "deployments/migration-payload.json"), "utf8"),
);
const payload = JSON.stringify(migration);
const snapshotHash = createHash("sha256").update(payload).digest("hex");
const manifest = JSON.parse(
  readFileSync(resolve(root, "deployments/migration-manifest.json"), "utf8"),
);
if (snapshotHash !== manifest.snapshotHash) {
  throw new Error("Migration payload hash does not match the manifest");
}

const env = readFileSync(resolve(root, "../.env"), "utf8");
const key = env
  .split(/\r?\n/)
  .find((line) => line.startsWith("GENLAYER_PRIVATE_KEY_0="))
  ?.split("=")[1]
  ?.trim();
if (!key) throw new Error("GENLAYER_PRIVATE_KEY_0 is missing");

const account = createAccount(key);
const client = createClient({ chain: testnetBradbury, account });
const hash = await client.writeContract({
  address: deployment.contractAddress,
  functionName: "import_snapshot",
  args: [payload, snapshotHash],
  leaderOnly: true,
});
console.log(`Bradbury snapshot import submitted: ${hash}`);
const receipt = await client.waitForTransactionReceipt({
  hash,
  status: TransactionStatus.ACCEPTED,
  retries: 360,
  interval: 3_000,
});
const leader = receipt.consensus_data?.leader_receipt?.[0];
const succeeded =
  receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN ||
  leader?.execution_result === "SUCCESS";
if (!succeeded) {
  throw new Error(
    JSON.stringify(receipt, (_key, value) =>
      typeof value === "bigint" ? value.toString() : value,
    ),
  );
}
deployment.migration = {
  ...deployment.migration,
  transactionHash: hash,
  snapshotHash,
  migratedRecords: manifest.migratedRecords,
  status: "ACCEPTED",
  executionResult: "FINISHED_WITH_RETURN",
  importedAt: new Date().toISOString(),
};
writeFileSync(deploymentPath, `${JSON.stringify(deployment, null, 2)}\n`);
console.log(JSON.stringify(deployment.migration, null, 2));
