import { createAccount, createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";
import { readFileSync } from "node:fs";
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
const contractAddress = "0x13856a9658BaDc8CfE25c098579Cd9BB21b9b7C9";

async function write(functionName, args, title) {
  console.log(`\n${title}...`);
  const hash = await client.writeContract({
    address: contractAddress,
    functionName,
    args,
  });
  console.log(`TX: ${hash}`);
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    retries: 120,
    interval: 3000,
  });
  const succeeded =
    receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN;
  if (!succeeded) {
    console.log("Failed:", receipt.txExecutionResultName);
    throw new Error("Transaction failed");
  }
  console.log(`✅ ${title} complete`);
  return hash;
}

async function main() {
  // Submit several signals
  await write(
    "submit_signal",
    [
      "SEN-001",
      "86 ug/m3",
      "2026-08-01T14:00:00Z",
      "Three consecutive elevated readings appeared downwind of active freight loading. The neighboring nitrogen sensor rose simultaneously and wind direction points from the loading area.",
      "https://github.com/AbstrusImad/fieldsignal",
      "",
    ],
    "Submitting signal 1 (PM2.5 elevated)",
  );

  await write(
    "submit_signal",
    [
      "SEN-003",
      "18%",
      "2026-08-01T14:30:00Z",
      "Soil moisture dropped below baseline during midday heat. Neighboring stations show similar patterns consistent with regional drought conditions.",
      "https://github.com/AbstrusImad/fieldsignal",
      "",
    ],
    "Submitting signal 2 (Soil moisture low)",
  );

  await write(
    "submit_signal",
    [
      "SEN-004",
      "5.2 mg/L",
      "2026-08-01T15:00:00Z",
      "Dissolved oxygen remained below the station baseline for forty minutes during an outgoing tide while turbidity increased at the paired harbor sensor.",
      "https://github.com/AbstrusImad/fieldsignal",
      "",
    ],
    "Submitting signal 3 (Dissolved oxygen low)",
  );

  // Resolve some signals to create incidents
  await write("resolve_signal", ["SIG-0001"], "Resolving signal 1");
  await write("resolve_signal", ["SIG-0002"], "Resolving signal 2");

  // Assign inspection to incident if created
  await write(
    "assign_inspection",
    [
      "INC-0001",
      "Verify physical condition and calibration, collect a co-located reference sample, document nearby activity, and publish time-aligned evidence.",
    ],
    "Assigning inspection to incident 1",
  );

  // Submit inspection findings
  await write(
    "submit_inspection",
    [
      "INS-0001",
      "Field inspection confirmed the device condition and compared its reading against a traceable reference instrument with timestamped context. The inlet was unobstructed and calibration checks passed.",
      "https://github.com/AbstrusImad/fieldsignal",
      "",
    ],
    "Submitting inspection findings",
  );

  // Review inspection
  await write("resolve_inspection", ["INS-0001"], "Reviewing inspection");

  console.log("\n✅ All transactions complete!");
  console.log("Contract:", contractAddress);
}

main().catch((e) => {
  console.error("Error:", e.message);
  process.exit(1);
});
