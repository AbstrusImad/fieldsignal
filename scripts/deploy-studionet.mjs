import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

const root = process.cwd();
const env = readFileSync(resolve(root, "../.env"), "utf8");
const key = env
  .split(/\r?\n/)
  .find((line) => line.startsWith("GENLAYER_PRIVATE_KEY_0="))
  ?.slice("GENLAYER_PRIVATE_KEY_0=".length)
  .trim();
if (!key) throw new Error("GENLAYER_PRIVATE_KEY_0 is missing");

const account = createAccount(key);
const client = createClient({ chain: studionet, account });
const source = readFileSync(resolve(root, "contracts/fieldsignal.py"), "utf8");
const code = new TextEncoder().encode(source);
const contractSha256 = createHash("sha256").update(code).digest("hex");
const hash = await client.deployContract({ code, args: [], leaderOnly: false });
console.log(`StudioNet deployment submitted: ${hash}`);

const receipt = await client.waitForTransactionReceipt({
  hash,
  status: TransactionStatus.ACCEPTED,
  retries: 180,
  interval: 3_000,
});
const leader = receipt.consensus_data?.leader_receipt?.[0];
const succeeded =
  receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN ||
  leader?.execution_result === "SUCCESS";
const contractAddress =
  receipt.data?.contractAddress ||
  receipt.data?.contract_address ||
  receipt.txDataDecoded?.contractAddress;
if (!succeeded || !contractAddress) {
  throw new Error(JSON.stringify(receipt, (_key, value) =>
    typeof value === "bigint" ? value.toString() : value,
  ));
}

const deployment = {
  network: "studionet",
  chainId: 61999,
  contract: "FieldSignal",
  contractAddress,
  transactionHash: hash,
  deployer: account.address,
  publisher: "AbstrusImad",
  explorer: "https://explorer-studio.genlayer.com",
  status: "ACCEPTED",
  executionResult: "FINISHED_WITH_RETURN",
  deployedAt: new Date().toISOString(),
  contractSha256,
  reviewRemediation: {
    authenticatedOperators: true,
    contractEvidenceRetrieval: true,
    recordedInspectorRole: true,
    requiredResponseConsensus: true,
  },
  seed: { transactions: {}, status: "PENDING" },
};
writeFileSync(
  resolve(root, "deployments/studionet.json"),
  `${JSON.stringify(deployment, null, 2)}\n`,
);
const frontendEnv = `VITE_CONTRACT_ADDRESS=${contractAddress}\nVITE_EXPLORER_URL=https://explorer-studio.genlayer.com\n`;
writeFileSync(resolve(root, "app/.env.production"), frontendEnv);
writeFileSync(resolve(root, "app/.env"), frontendEnv);
console.log(JSON.stringify(deployment, null, 2));
