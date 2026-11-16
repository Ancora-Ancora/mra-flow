#!/usr/bin/env node
// mra-flow UI smoke runner: level 2 of /mra-qa-ui.
//
//   node <orchestrator>/.mra-flow/qa-ui/smoke.mjs <plan.json>
//
// Run it with the current directory where `playwright` is installed
// (npm i --no-save playwright@<version>; npx playwright install chromium).
// Loads every page x viewport of the plan with each page's role logged in,
// saves a screenshot per page and prints ONE compact JSON summary: passing
// pages are listed briefly, failing pages carry the details. Exit code: 0 all
// pages pass, 1 some page fails, 2 the plan or the setup is wrong.
import { createRequire } from "node:module";
import { mkdirSync, readFileSync } from "node:fs";
import path from "node:path";

const VIEWPORTS = { desktop: { width: 1366, height: 900 }, mobile: { width: 390, height: 844 } };
const MAX_ITEMS = 5;
const CLIP = 200;

function die(message) {
  console.error(`Error: ${message}`);
  process.exit(2);
}

const clip = (s) => (s.length > CLIP ? `${s.slice(0, CLIP)}...` : s);

function expand(value) {
  return String(value).replace(/\$\{(\w+)\}/g, (_, name) => {
    if (!(name in process.env)) die(`environment variable ${name} is not set`);
    return process.env[name];
  });
}

function loadPlaywright() {
  try {
    return createRequire(path.join(process.cwd(), "noop.js"))("playwright");
  } catch {
    die(`playwright not found from ${process.cwd()}: run 'npm i --no-save playwright@<version>' ` +
        "and 'npx playwright install chromium' there");
  }
}

function loadPlan(file) {
  let plan;
  try {
    plan = JSON.parse(readFileSync(file, "utf8"));
  } catch (exc) {
    die(`cannot read plan ${file}: ${exc.message}`);
  }
  if (typeof plan.baseUrl !== "string") die("plan.baseUrl is missing");
  if (!Array.isArray(plan.pages) || plan.pages.length === 0) die("plan.pages is empty");
  plan.roles ??= {};
  for (const page of plan.pages) {
    if (typeof page.path !== "string") die(`page without path: ${JSON.stringify(page)}`);
    page.role ??= "anonymous";
    if (page.role !== "anonymous" && !(page.role in plan.roles)) die(`page ${page.path}: unknown role ${page.role}`);
    for (const v of page.viewports ?? ["desktop"]) if (!(v in VIEWPORTS)) die(`page ${page.path}: unknown viewport ${v}`);
  }
  return plan;
}

async function runSteps(page, steps, baseUrl, timeout) {
  for (const step of steps) {
    if (step.goto !== undefined) await page.goto(new URL(expand(step.goto), baseUrl).href, { timeout });
    else if (step.fill !== undefined) await page.fill(step.fill, expand(step.value ?? ""), { timeout });
    else if (step.click !== undefined) await page.click(step.click, { timeout });
    else if (step.waitForUrl !== undefined) await page.waitForURL(step.waitForUrl, { timeout });
    else if (step.waitFor !== undefined) await page.waitForSelector(step.waitFor, { timeout });
    else throw new Error(`unknown step ${JSON.stringify(step)}`);
  }
}

async function login(browser, plan, role, timeout) {
  const steps = plan.roles[role]?.login ?? [];
  if (steps.length === 0) return undefined;
  const context = await browser.newContext();
  try {
    await runSteps(await context.newPage(), steps, plan.baseUrl, timeout);
    return await context.storageState();
  } finally {
    await context.close();
  }
}

function matcher(patterns) {
  const res = (patterns ?? []).map((p) => new RegExp(p));
  return (text) => res.some((re) => re.test(text));
}

async function checkPage(browser, plan, spec, viewport, state, outDir, opts) {
  const context = await browser.newContext({ viewport: VIEWPORTS[viewport], storageState: state });
  const page = await context.newPage();
  const consoleErrors = [];
  const failedRequests = [];
  page.on("console", (msg) => {
    if (msg.type() === "error" && !opts.ignoreConsole(msg.text())) consoleErrors.push(clip(msg.text()));
  });
  page.on("pageerror", (err) => consoleErrors.push(clip(`uncaught: ${err.message}`)));
  page.on("response", (res) => {
    if (res.status() >= 400 && !opts.ignoreRequests(res.url())) failedRequests.push(`${res.status()} ${clip(res.url())}`);
  });
  page.on("requestfailed", (req) => {
    if (!opts.ignoreRequests(req.url())) failedRequests.push(`failed ${clip(req.url())}: ${req.failure()?.errorText ?? ""}`);
  });

  const result = { role: spec.role, path: spec.path, viewport };
  try {
    const response = await page.goto(new URL(spec.path, plan.baseUrl).href, { timeout: opts.timeout });
    result.status = response?.status();
    await page.waitForTimeout(opts.settleMs);
    const missing = [];
    for (const selector of spec.expect ?? []) {
      try {
        await page.locator(selector).first().waitFor({ state: "visible", timeout: opts.expectTimeout });
      } catch {
        missing.push(selector);
      }
    }
    if (missing.length) result.missing = missing;
  } catch (exc) {
    result.error = clip(exc.message.split("\n")[0]);
  }
  const name = `${spec.role}-${spec.path.replace(/[^a-z0-9]+/gi, "_").replace(/^_|_$/g, "") || "root"}-${viewport}.png`;
  const screenshot = path.join(outDir, name);
  await page.screenshot({ path: screenshot, fullPage: true }).catch(() => {});
  await context.close();

  if (consoleErrors.length) result.consoleErrors = consoleErrors.slice(0, MAX_ITEMS);
  if (failedRequests.length) result.failedRequests = failedRequests.slice(0, MAX_ITEMS);
  result.ok = !result.error && !result.missing && !result.consoleErrors && !result.failedRequests &&
              (result.status === undefined || result.status < 400);
  if (!result.ok) result.screenshot = screenshot;
  return result;
}

async function main() {
  const file = process.argv[2] ?? die("usage: node smoke.mjs <plan.json>");
  const plan = loadPlan(file);
  const { chromium } = loadPlaywright();
  const outDir = path.resolve(path.dirname(file), plan.outDir ?? "screenshots");
  mkdirSync(outDir, { recursive: true });
  const opts = {
    timeout: plan.timeoutMs ?? 15000,
    expectTimeout: plan.expectTimeoutMs ?? 5000,
    settleMs: plan.settleMs ?? 500,
    ignoreConsole: matcher(plan.ignoreConsole),
    ignoreRequests: matcher(plan.ignoreRequests),
  };

  const browser = await chromium.launch();
  const results = [];
  try {
    const states = {};
    for (const role of new Set(plan.pages.map((p) => p.role))) {
      try {
        states[role] = role === "anonymous" ? undefined : await login(browser, plan, role, opts.timeout);
      } catch (exc) {
        states[role] = new Error(clip(exc.message.split("\n")[0]));
      }
    }
    for (const spec of plan.pages) {
      for (const viewport of spec.viewports ?? ["desktop"]) {
        const state = states[spec.role];
        if (state instanceof Error) {
          results.push({ role: spec.role, path: spec.path, viewport, ok: false, error: `login failed: ${state.message}` });
        } else {
          results.push(await checkPage(browser, plan, spec, viewport, state, outDir, opts));
        }
      }
    }
  } finally {
    await browser.close();
  }

  const failed = results.filter((r) => !r.ok);
  console.log(JSON.stringify({
    ok: failed.length === 0,
    checked: results.length,
    failed,
    passed: results.filter((r) => r.ok).map((r) => `${r.role} ${r.path} ${r.viewport}`),
    screenshots: outDir,
  }, null, 1));
  process.exitCode = failed.length ? 1 : 0; // not process.exit(): let stdout flush
}

main().catch((exc) => die(exc.stack ?? String(exc)));
