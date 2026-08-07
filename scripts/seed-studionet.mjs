import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

const root = process.cwd();
const deploymentPath = resolve(root, "deployments/studionet.json");
const deployment = JSON.parse(readFileSync(deploymentPath, "utf8"));
const env = readFileSync(resolve(root, "../.env"), "utf8");
const key = env
  .split(/\r?\n/)
  .find((line) => line.startsWith("GENLAYER_PRIVATE_KEY_0="))
  ?.slice("GENLAYER_PRIVATE_KEY_0=".length)
  .trim();
if (!key) throw new Error("GENLAYER_PRIVATE_KEY_0 is missing");

const account = createAccount(key);
if (deployment.deployer.toLowerCase() !== account.address.toLowerCase()) {
  throw new Error("StudioNet deployment was not created by account 0");
}
const client = createClient({ chain: studionet, account });
deployment.seed ??= { transactions: {}, status: "PENDING" };
deployment.seed.transactions ??= {};
const save = () => writeFileSync(
  deploymentPath,
  `${JSON.stringify(deployment, null, 2)}\n`,
);
const isBusy = (error) => /Server busy|rate limit|-32429|-32028|429/i.test(
  String(error?.details || error?.message || error),
);

async function submit(stage, functionName, args) {
  if (["ACCEPTED", "SATISFIED_BY_STATE"].includes(deployment.seed.transactions[stage]?.status)) return;
  let hash = deployment.seed.transactions[stage]?.hash;
  if (!hash) {
    for (let attempt = 1; attempt <= 30; attempt += 1) {
      try {
        hash = await client.writeContract({
          address: deployment.contractAddress,
          functionName,
          args,
          leaderOnly: false,
        });
        break;
      } catch (error) {
        if (!isBusy(error) || attempt === 30) throw error;
        await new Promise((done) => setTimeout(done, 10_000));
      }
    }
    deployment.seed.transactions[stage] = {
      hash,
      functionName,
      status: "SUBMITTED",
      submittedAt: new Date().toISOString(),
    };
    save();
    console.log(`${stage}: ${hash}`);
  }
  let receipt;
  for (let attempt = 1; attempt <= 12; attempt += 1) {
    try {
      receipt = await client.waitForTransactionReceipt({
        hash,
        status: TransactionStatus.ACCEPTED,
        retries: 180,
        interval: 6_000,
      });
      break;
    } catch (error) {
      if (!isBusy(error) || attempt === 12) throw error;
      await new Promise((done) => setTimeout(done, 65_000));
    }
  }
  const leader = receipt.consensus_data?.leader_receipt?.[0];
  const succeeded =
    receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN ||
    leader?.execution_result === "SUCCESS";
  if (!succeeded) {
    throw new Error(`${stage} failed: ${JSON.stringify(receipt, (_key, value) =>
      typeof value === "bigint" ? value.toString() : value,
    )}`);
  }
  deployment.seed.transactions[stage].status = "ACCEPTED";
  deployment.seed.transactions[stage].acceptedAt = new Date().toISOString();
  save();
}

async function ensureSignalResolved(stage, signalId) {
  const signals = await client.readContract({
    address: deployment.contractAddress,
    functionName: "get_signals",
    args: [],
    jsonSafeReturn: true,
  });
  const signal = signals.find((item) => item.id === signalId);
  if (signal?.status === "RESOLVED") {
    const previous = deployment.seed.transactions[stage];
    deployment.seed.transactions[stage] = {
      functionName: "resolve_signal",
      status: "SATISFIED_BY_STATE",
      stateProof: `${signalId}:RESOLVED:${signal.evidence_digest}`,
      supersededHash: previous?.status === "SUBMITTED" ? previous.hash : undefined,
      verifiedAt: new Date().toISOString(),
    };
    save();
    return;
  }
  await submit(stage, "resolve_signal", [signalId]);
}

const base = "https://raw.githubusercontent.com/AbstrusImad/fieldsignal/main/docs/evidence";
await submit("configure-owner-access", "configure_access", [
  account.address,
  true,
  true,
  "STA-001",
]);
await submit("signal-pm25", "submit_signal", [
  "SEN-001",
  "86 ug/m3",
  "2026-08-05T12:00:00Z",
  "Three consecutive elevated readings were corroborated by a co-located reference instrument while freight loading remained active upwind.",
  `${base}/signal-pm25.md`,
]);
await ensureSignalResolved("resolve-pm25", "SIG-0001");
await submit("signal-soil", "submit_signal", [
  "SEN-003",
  "22%",
  "2026-08-05T12:30:00Z",
  "Soil moisture fell below baseline during a dry interval while nearby plots showed similar reductions and diagnostics remained clean.",
  `${base}/signal-soil.md`,
]);
await ensureSignalResolved("resolve-soil", "SIG-0002");
await submit("signal-wind", "submit_signal", [
  "SEN-007",
  "92 m/s",
  "2026-08-05T13:00:00Z",
  "The value jumped from six to ninety-two within one interval, neighboring stations remained ordinary, and diagnostics reported checksum failures.",
  `${base}/signal-wind.md`,
]);
await ensureSignalResolved("resolve-wind", "SIG-0003");

const incidents = await client.readContract({
  address: deployment.contractAddress,
  functionName: "get_incidents",
  args: [],
  jsonSafeReturn: true,
});
const pm25Incident = incidents.find((item) => item.signal_id === "SIG-0001");
if (!pm25Incident) throw new Error("PM2.5 consensus did not open an incident");

await submit("assign-pm25", "assign_inspection", [
  pm25Incident.id,
  account.address,
  "Inspect SEN-001, collect a co-located reference reading, document source conditions, and publish a time-aligned public evidence record.",
]);
await submit("inspect-pm25", "submit_inspection", [
  "INS-0001",
  "The authorized inspector confirmed the inlet was clear, collected a co-located reference reading, documented active diesel equipment upwind, and increased sampling cadence.",
  `${base}/inspection-pm25.md`,
]);
await submit("resolve-inspection-pm25", "resolve_inspection", ["INS-0001"]);

deployment.seed.status = "ACCEPTED";
deployment.seed.transactionCount = Object.keys(deployment.seed.transactions).length;
deployment.seed.completedAt = new Date().toISOString();
save();
console.log(JSON.stringify(deployment.seed, null, 2));
