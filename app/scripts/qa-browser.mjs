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
  await page.getByText("FIELD GUIDE", { exact: true }).click();
  await page.waitForTimeout(500);
  const guide = await page.locator(".field-guide").evaluate((element) => ({
    visible: getComputedStyle(element).opacity === "1",
    reviewerPath: element.innerText.includes("REVIEWER QUICK START"),
    snapSafe: element.innerText.includes("No MetaMask Snaps method is used"),
  }));
  await page.screenshot({
    path: `C:/tmp/fieldsignal-${viewport.name}-studionet.png`,
  });
  results.push({ viewport: viewport.name, ...landing, guide, errors });
  await page.close();
}
await browser.close();
console.log(JSON.stringify(results, null, 2));
