import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
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
  await page.goto("http://127.0.0.1:4174/fieldsignal/", {
    waitUntil: "networkidle",
  });
  const result = await page.evaluate(() => ({
    title: document.title,
    heading: document.querySelector("h1")?.innerText || "",
    network: document.body.innerText.includes("STUDIONET"),
    walletControl: document.body.innerText.includes("WITH WALLET"),
    horizontalOverflow:
      document.documentElement.scrollWidth > document.documentElement.clientWidth,
  }));
  await page.screenshot({
    path: `C:/tmp/fieldsignal-${viewport.name}-bradbury.png`,
    fullPage: true,
  });
  results.push({ viewport: viewport.name, ...result, errors });
  await page.close();
}
await browser.close();
console.log(JSON.stringify(results, null, 2));
