import { createAccount, createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = process.cwd();
const env = readFileSync(resolve(root, ".env"), "utf8");
const key = env
  .split(/\r?\n/)
  .find((line) => line.startsWith("GENLAYER_PRIVATE_KEY_0="))
  ?.split("=")[1]
  ?.trim();
if (!key) throw new Error("GENLAYER_PRIVATE_KEY_0 is missing");

const account = createAccount(key);
const client = createClient({ chain: testnetBradbury, account });
const contractSource = readFileSync(resolve(root, "contracts/fieldsignal.py"), "utf8");
const code = new TextEncoder().encode(contractSource);

console.log("Deploying with genesis data (migration_mode=false)...");
const hash = await client.deployContract({ code, args: [false] });
console.log(`TX: ${hash}`);

const receipt = await client.waitForTransactionReceipt({
  hash,
  status: TransactionStatus.ACCEPTED,
  retries: 120,
  interval: 3_000,
});

const leader = receipt.consensus_data?.leader_receipt?.[0];
const succeeded =
  receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN ||
  leader?.execution_result === "SUCCESS";

const contractAddress =
  receipt.contractAddress ||
  receipt.data?.contractAddress ||
  receipt.data?.contract_address ||
  receipt.txDataDecoded?.contractAddress;

console.log("Receipt keys:", Object.keys(receipt));
console.log("Contract address from receipt:", contractAddress);

if (!succeeded) {
  throw new Error(
    JSON.stringify(receipt, (_key, value) =>
      typeof value === "bigint" ? value.toString() : value,
    ),
  );
}

if (!contractAddress) {
  console.log("Full receipt:", JSON.stringify(receipt, null, 2));
  throw new Error("Could not extract contract address from receipt");
}

console.log(`✅ Contract deployed: ${contractAddress}`);

const deployment = {
  network: "testnet-bradbury",
  chainId: 4221,
  contractAddress,
  transactionHash: hash,
  deployer: account.address,
  publisher: "AbstrusImad",
  explorer: "https://explorer-bradbury.genlayer.com",
  status: "ACCEPTED",
  deployedAt: new Date().toISOString(),
  migration: false,
  genesis: true,
};

writeFileSync(resolve(root, "deployments/bradbury-genesis.json"), JSON.stringify(deployment, null, 2));
writeFileSync(
  resolve(root, "app/.env.production"),
  `VITE_CONTRACT_ADDRESS=${contractAddress}\nVITE_EXPLORER_URL=https://explorer-bradbury.genlayer.com\n`,
);

console.log("✅ Metadata saved to deployments/bradbury-genesis.json");
console.log("✅ Frontend .env.production updated");
