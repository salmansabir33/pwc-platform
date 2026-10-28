import assert from "node:assert/strict";
import { chromium } from "@playwright/test";
const fixture = JSON.parse(process.env.PWC_SYNTHETIC_BROWSER_FIXTURE);
const browser = await chromium.launch({
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}),
  args: ["--no-proxy-server", "--host-resolver-rules=MAP ngo.pwc.invalid 127.0.0.1,MAP ops.pwc.invalid 127.0.0.1"],
});
const contexts = [];
async function portal(name, host = "ngo.pwc.invalid") {
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  contexts.push(context);
  await context.addCookies(fixture.cookies[name]);
  const page = await context.newPage();
  await page.goto(`https://${host}:${fixture.port}/`);
  await page.getByRole("button", { name: "Check personal session", exact: true }).click();
  await page.getByText("Personal session checked. No active NGO authority.", { exact: true }).waitFor();
  return page;
}
try {
  const foreign = await portal("foreign");
  const owner = await portal("owner");
  const ops = await portal("ops", "ops.pwc.invalid");
  for (const page of [owner, ops]) {
    await page.getByRole("button", { name: "Search registry", exact: true }).click();
    await page.getByText("Public Synthetic Welfare", { exact: true }).waitFor();
    await page.getByRole("button", { name: "Refresh rollout policy", exact: true }).click();
    await page.getByText("offline_initial_2026_10_27", { exact: true }).waitFor();
    assert.equal(await page.getByRole("button", { name: /Approve|Grant activation/ }).count(), 0);
  }
  const foreignResult = await foreign.evaluate(async id => {
    const r = await fetch(`/api/v1/registry/workspace/drafts/${id}/`);
    return { status: r.status, body: await r.json() };
  }, fixture.source);
  assert.equal(foreignResult.status, 404);
  assert.equal(foreignResult.body.error.code, "NOT_FOUND");
  await foreign.getByRole("button", { name: "Refresh history", exact: true }).click();
  await foreign.getByText("No matching historical applications.", { exact: true }).waitFor();
  await owner.getByLabel("Application state", { exact: true }).selectOption("draft");
  await owner.getByRole("button", { name: "Refresh history", exact: true }).click();
  await owner.getByText("Synthetic Welfare", { exact: true }).waitFor();
  await owner.getByRole("button", { name: "Corrupt next CSRF (test only)", exact: true }).click();
  await owner.getByRole("button", { name: "Withdraw application", exact: true }).click();
  await owner.getByRole("button", { name: "Confirm withdrawal", exact: true }).click();
  await owner.getByText("No checked personal session.", {exact: true}).waitFor();
  assert.equal(await owner.getByText("Synthetic Welfare", {exact: true}).count(), 0);
  await owner.getByRole("button", { name: "Check personal session", exact: true }).click();
  await owner.getByText("Personal session checked. No active NGO authority.", {exact: true}).waitFor();
  await owner.getByLabel("Application state", { exact: true }).selectOption("draft");
  await owner.getByRole("button", { name: "Refresh history", exact: true }).click();
  await owner.getByText("Synthetic Welfare", {exact: true}).waitFor();
  await owner.getByRole("button", { name: "Discard next withdrawal response (test only)", exact: true }).click();
  await owner.getByRole("button", { name: "Withdraw application", exact: true }).click();
  await owner.getByRole("button", { name: "Confirm withdrawal", exact: true }).click();
  await owner.getByText("Withdrawal outcome not confirmed", { exact: true }).waitFor();
  await owner.getByRole("button", { name: "Check withdrawal status", exact: true }).click();
  await owner.getByText(/Server currently reports Withdrawn · revision 2/).waitFor();
  await owner.getByRole("button", { name: "Refresh history", exact: true }).click();
  await owner.getByText("No matching historical applications.", { exact: true }).waitFor();
  await owner.getByLabel("Application state", { exact: true }).selectOption("withdrawn");
  await owner.getByRole("button", { name: "Refresh history", exact: true }).click();
  await owner.getByText("Stale source", { exact: false }).waitFor();
  assert.equal(await owner.getByRole("button", { name: "Withdraw application", exact: true }).count(), 0);
  const duplicate = await owner.evaluate(async id => {
    const csrf = await (await fetch("/api/v1/auth/csrf/")).json();
    return (await fetch(`/api/v1/registry/drafts/${id}/withdraw/`, { method: "POST", headers: {"Content-Type":"application/json", "X-CSRFToken": csrf.csrf_token}, body: JSON.stringify({ revision: 1 }) })).status;
  }, fixture.source);
  assert.equal(duplicate, 409);
  const csrf = await foreign.evaluate(async id => (await fetch(`/api/v1/registry/drafts/${id}/withdraw/`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ revision: 1 }) })).status, fixture.source);
  assert.equal(csrf, 403);
  // Cookie copied to another portal is not an accepted portal-bound session.
  const wrong = await browser.newContext({ignoreHTTPSErrors: true});
  contexts.push(wrong);
  await wrong.addCookies(fixture.cookies.owner.map(cookie => ({...cookie, url: `https://ops.pwc.invalid:${fixture.port}/`})));
  const wrongPage = await wrong.newPage();
  await wrongPage.goto(`https://ops.pwc.invalid:${fixture.port}/`);
  const wrongStatus = await wrongPage.evaluate(async () => (await fetch("/api/v1/auth/me/")).status);
  assert.equal(wrongStatus, 401);
  await owner.getByRole("button", {name: "End personal session (test only)", exact: true}).click();
  await owner.getByText("No checked personal session.", {exact: true}).waitFor();
  assert.equal(await owner.getByText("Synthetic Welfare", {exact: true}).count(), 0);
  await owner.getByRole("button", {name: "Check personal session", exact: true}).click();
  await owner.getByText(/Session unavailable or expired/).waitFor();
  console.log("Actual direct-TLS browser assertions passed: both public portals, policy, owner/foreign, filtered lost-response reconciliation, revision/stale, duplicate conflict, CSRF denial. Synthetic certificates/identities only.");
} finally {
  for (const context of contexts) await context.close();
  await browser.close();
}
