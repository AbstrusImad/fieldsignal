import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

export const contractAddress =
  import.meta.env.VITE_CONTRACT_ADDRESS ||
  "0x42a6982fA6bAD35b3FE4A0E21c162a07195D18Cb";
export const explorerUrl =
  import.meta.env.VITE_EXPLORER_URL ||
  "https://explorer-bradbury.genlayer.com";
export const publicClient = createClient({ chain: testnetBradbury });

const stringify = (value) => {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

const clean = (value) => {
  let text = stringify(value || "").trim();
  try {
    const parsed = JSON.parse(text);
    text = typeof parsed === "string" ? parsed : stringify(parsed?.message || parsed);
  } catch {
    // GenVM errors are frequently plain text.
  }
  return text
    .replace(/^\[(EXPECTED|EXTERNAL|TRANSIENT|LLM_ERROR)\]\s*/i, "")
    .replace(/^UserError:\s*/i, "")
    .trim();
};

const busy = (error) => {
  const text = stringify(error?.details || error?.message || error);
  return text.includes("Server busy") || text.includes("-32028") || text.includes("429");
};

async function retry(operation, attempts = 10) {
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      if (!busy(error) || attempt === attempts) throw error;
      await new Promise((done) => setTimeout(done, attempt * 1_200));
    }
  }
}

export async function connectWallet({ silent = false } = {}) {
  if (!window.ethereum) {
    if (silent) return null;
    throw new Error("No browser wallet detected.");
  }
  const accounts = await window.ethereum.request({
    method: silent ? "eth_accounts" : "eth_requestAccounts",
  });
  const address = accounts?.[0];
  if (!address) return null;
  const client = createClient({ chain: testnetBradbury, account: address });
  if (!silent) await client.connect("testnetBradbury");
  return { address, client };
}

export const readContract = (functionName, args = []) =>
  retry(() =>
    publicClient.readContract({
      address: contractAddress,
      functionName,
      args,
      jsonSafeReturn: true,
    }),
  );

const leader = (receipt) =>
  receipt?.consensus_data?.leader_receipt?.[0] ||
  receipt?.consensusData?.leaderReceipt?.[0];

const decode = (value) => {
  if (typeof value !== "string" || !value) return "";
  try {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(padded), (item) => item.charCodeAt(0));
    return [1, 2, 3].includes(bytes[0])
      ? new TextDecoder().decode(bytes.slice(1))
      : "";
  } catch {
    return "";
  }
};

function receiptError(receipt) {
  const record = leader(receipt);
  const candidates = [
    decode(record?.result),
    ...Object.values(record?.eq_outputs || {}).map(decode),
    record?.genvm_result?.error_description,
    record?.genvm_result?.stderr,
    record?.result?.payload?.readable,
    receipt?.error,
  ];
  for (const item of candidates) {
    const message = clean(item);
    if (message && message !== "FINISHED_WITH_ERROR") return message;
  }
  return "The contract rejected this action.";
}

export function formatError(error) {
  for (const item of [
    error?.shortMessage,
    error?.details,
    error?.cause?.message,
    error?.message,
    error,
  ]) {
    const message = clean(item);
    if (message && message !== "[object Object]") return message;
  }
  return "The action could not be completed.";
}

export async function writeContract({
  client,
  functionName,
  args = [],
  onStage,
}) {
  if (!client) throw new Error("Connect your wallet first.");
  onStage?.("signature");
  await client.connect("testnetBradbury");
  const hash = await retry(() =>
    client.writeContract({ address: contractAddress, functionName, args }),
  );
  onStage?.("consensus", hash);
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: TransactionStatus.ACCEPTED,
    retries: 120,
    interval: 3_000,
  });
  const succeeded =
    receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN ||
    leader(receipt)?.execution_result === "SUCCESS";
  if (!succeeded) {
    const error = new Error(receiptError(receipt));
    error.hash = hash;
    error.receipt = receipt;
    throw error;
  }
  onStage?.("accepted", hash);
  return { hash, receipt };
}
