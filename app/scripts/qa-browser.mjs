import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
const baseUrl = process.env.QA_URL || "http://127.0.0.1:4174/fieldsignal/";
const results = [];
for (const viewport of [
  { name: "desktop", width: 1440, height: 960 },
  { name: "mobile", width: 390, height: 844 },
]) {
  const page = await browser.newPage({
    viewport: { width: viewport.width, height: viewport.height },
  });
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(baseUrl, {
    waitUntil: "networkidle",
  });
  const landing = await page.evaluate(() => ({
    title: document.title,
    heading: document.querySelector("h1")?.innerText || "",
    network: document.body.innerText.includes("STUDIONET"),
    walletControl: document.body.innerText.includes("WITH WALLET"),
    horizontalOverflow:
      document.documentElement.scrollWidth > document.documentElement.clientWidth,
  }));
  const guideHref = await page.locator("a.field-guide-trigger").getAttribute("href");
  await page.screenshot({
    path: `C:/tmp/fieldsignal-${viewport.name}-landing.png`,
  });

  const guidePage = await browser.newPage({
    viewport: { width: viewport.width, height: viewport.height },
  });
  const guideErrors = [];
  guidePage.on("console", (message) => {
    if (message.type() === "error") guideErrors.push(message.text());
  });
  guidePage.on("pageerror", (error) => guideErrors.push(error.message));
  await guidePage.goto(new URL("guide/", baseUrl).href, { waitUntil: "networkidle" });
  const guide = await guidePage.evaluate(() => ({
    title: document.title,
    chapters: document.querySelectorAll(".guide-chapter").length,
    detailedPath: document.body.innerText.includes("Operate FieldSignal from reading to verified response"),
    snapSafe: document.body.innerText.includes("It never invokes"),
    rolesDocumented: document.body.innerText.includes("Roles and permissions"),
    horizontalOverflow:
      document.documentElement.scrollWidth > document.documentElement.clientWidth,
  }));
  await guidePage.screenshot({
    path: `C:/tmp/fieldsignal-${viewport.name}-guide.png`,
    fullPage: true,
  });
  await guidePage.close();

  results.push({
    viewport: viewport.name,
    ...landing,
    guideHref,
    guide,
    errors: [...errors, ...guideErrors],
  });
  await page.close();
}

const connected = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await connected.addInitScript(() => {
  localStorage.setItem("fieldsignal:wallet-connected", "true");
  window.ethereum = {
    request: async ({ method }) => {
      if (method === "eth_accounts" || method === "eth_requestAccounts") {
        return ["0x95803126315A05E642D8E46CE1d77eA2199a2A6E"];
      }
      throw new Error(`Unexpected QA wallet method: ${method}`);
    },
  };
});
await connected.goto(baseUrl, { waitUntil: "domcontentloaded" });
const loaderVisible = await connected
  .locator(".chain-loader")
  .waitFor({ state: "visible", timeout: 8_000 })
  .then(() => true)
  .catch(() => false);
await connected.locator(".chain-loader").waitFor({ state: "hidden", timeout: 90_000 });
const connectedState = {
  loaderVisible,
  surveyLoaded: await connected.getByText("INSTRUMENT FIELD RECORD", { exact: true }).isVisible(),
};
for (const target of ["TRACES", "RESPONSE", "ACCESS"]) {
  await connected.getByRole("button", { name: new RegExp(target) }).click();
  connectedState[`${target.toLowerCase()}LoaderVisible`] = await connected
    .locator(".chain-loader")
    .waitFor({ state: "visible", timeout: 8_000 })
    .then(() => true)
    .catch(() => false);
  await connected.locator(".chain-loader").waitFor({ state: "hidden", timeout: 90_000 });
}
connectedState.accessRegistryVisible = await connected
  .getByText("ON-CHAIN FIELD CREDENTIALS", { exact: true })
  .isVisible();
await connected.screenshot({ path: "C:/tmp/fieldsignal-desktop-access.png" });
await connected.close();

const unauthorized = await browser.newPage({ viewport: { width: 1280, height: 900 } });
await unauthorized.addInitScript(() => {
  localStorage.setItem("fieldsignal:wallet-connected", "true");
  window.ethereum = {
    request: async ({ method }) => {
      if (method === "eth_accounts" || method === "eth_requestAccounts") {
        return ["0x1111111111111111111111111111111111111111"];
      }
      throw new Error(`Unexpected QA wallet method: ${method}`);
    },
  };
});
await unauthorized.goto(baseUrl, { waitUntil: "domcontentloaded" });
await unauthorized.locator(".chain-loader").waitFor({ state: "hidden", timeout: 90_000 });
await unauthorized.getByRole("button", { name: /Log reading requires an active operator role/i }).click();
const unauthorizedGuard = {
  roleGuardVisible: await unauthorized.getByText("Operator authorization required", { exact: true }).isVisible(),
  reasonVisible: await unauthorized.getByText(/is not an active FieldSignal operator/).isVisible(),
};
await unauthorized.getByRole("button", { name: /Open access registry/i }).click();
await unauthorized.locator(".chain-loader").waitFor({ state: "hidden", timeout: 90_000 });
unauthorizedGuard.accessRegistryReached = await unauthorized
  .getByText("ON-CHAIN FIELD CREDENTIALS", { exact: true })
  .isVisible();
await unauthorized.close();
await browser.close();
console.log(JSON.stringify({ viewports: results, connectedState, unauthorizedGuard }, null, 2));
