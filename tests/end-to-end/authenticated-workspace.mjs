import assert from "node:assert/strict";
import { request as httpsRequest } from "node:https";
import { readFileSync } from "node:fs";
import { createHmac } from "node:crypto";
import axe from "axe-core";
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
  const page = await context.newPage();
  await page.goto(`https://${host}:${fixture.port}/`);
  await page.setViewportSize({width: 320, height: 844});
  for (const locale of ["en", "ur"]) {
    if (locale === "ur") await page.getByRole("button", {name: "Toggle locale"}).click();
    await page.addScriptTag({content: axe.source});
    const violations = await page.evaluate(async () => (await window.axe.run(document, {runOnly: {type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"]}})).violations.map(v => v.id));
    assert.deepEqual(violations, []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  }
  await page.getByRole("button", {name: "Toggle locale"}).click();
  const anonymous = await page.evaluate(async () => (await fetch("/api/v1/registry/workspace/")).status);
  assert.equal(anonymous, 401);
  await signIn(page, name);
  return page;
}
function totp(secret, stepOffset = 1) {
  const bits = [...secret].map(c => "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567".indexOf(c).toString(2).padStart(5, "0")).join("");
  const key = Buffer.from((bits.match(/.{8}/g) || []).map(b => parseInt(b, 2)));
  const counter = Buffer.alloc(8); counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000) + stepOffset));
  const hash = createHmac("sha1", key).update(counter).digest(); const offset = hash[19] & 15;
  return String((hash.readUInt32BE(offset) & 0x7fffffff) % 1000000).padStart(6, "0");
}
async function signIn(page, name, recovery = false) {
  await page.getByLabel("Email", {exact: true}).fill(fixture.accounts[name]);
  await page.getByLabel("Password", {exact: true}).fill(fixture.password);
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  if (name === "mfa") {
    await page.getByText("Second factor required. This is not an authenticated session.", {exact: true}).waitFor();
    assert.equal(await page.getByRole("button", {name: "Refresh history"}).isDisabled(), true);
    if (recovery) await page.getByLabel("Second factor method", {exact: true}).selectOption("recovery_code");
    await page.getByLabel("Second factor code", {exact: true}).fill(recovery ? fixture.recoveryCode : totp(fixture.mfaSecret));
    await page.getByRole("button", {name: "Confirm second factor", exact: true}).click();
  }
  await page.getByText(recovery ? "Recovery-restricted session. Private history cleared; recovery is not a grant." : "Personal session checked. No active NGO authority.", {exact: true}).waitFor();
  const cookies = await page.context().cookies();
  const session = cookies.find(c => c.name === "__Host-pwc_session");
  assert.ok(session); assert.equal(session.httpOnly, true); assert.equal(session.secure, true);
  assert.equal(session.sameSite, "Lax"); assert.equal(session.path, "/");
  assert.equal(session.domain, new URL(page.url()).hostname);
  assert.equal(await page.evaluate(() => document.cookie.includes("__Host-pwc_session=")), false);
  assert.deepEqual(await page.evaluate(() => ({local: Object.keys(localStorage), session: Object.keys(sessionStorage)})), {local: [], session: []});
  assert.equal(new URL(page.url()).search, ""); assert.equal(new URL(page.url()).hash, "");
}
async function tlsRequest(page, path, headers, method = "GET") {
  const cookies = (await page.context().cookies()).map(c => `${c.name}=${c.value}`).join("; ");
  return new Promise((resolve, reject) => {
    const request = httpsRequest({hostname: "127.0.0.1", port: fixture.port, servername: "ngo.pwc.invalid", ca: readFileSync(fixture.certificate), path, method,
      headers: {Host: `ngo.pwc.invalid:${fixture.port}`, Cookie: cookies, ...headers}}, response => { response.resume(); response.on("end", () => resolve(response.statusCode)); });
    request.on("error", () => reject(new Error("Synthetic TLS probe failed (details redacted)")));
    request.end();
  });
}
async function invitationCeremony(item, locale) {
  const context = await browser.newContext({ignoreHTTPSErrors: true}); contexts.push(context);
  const page = await context.newPage();
  await page.setViewportSize({width: 390, height: 844});
  await page.goto(`https://ngo.pwc.invalid:${fixture.port}/account/invite#invitation_id=${item.id}&token=${item.token}`);
  if (locale === "ur") await page.getByRole("button", {name: "Toggle locale"}).click();
  await page.getByRole("button", {name: "Begin invitation (test only)"}).click();
  const label = (en, ur) => locale === "ur" ? ur : en;
  assert.equal(new URL(page.url()).hash, "");
  await page.getByLabel(label("Your invitation email", "آپ کی دعوتی ای میل"), {exact: true}).fill(item.recipient);
  await page.getByRole("button", {name: label("Request email proof", "ای میل کوڈ کی درخواست"), exact: true}).click();
  await page.getByLabel(label("Email confirmation proof", "ای میل تصدیقی کوڈ"), {exact: true}).waitFor();
  const proof = JSON.parse(readFileSync(fixture.invitationMailbox, "utf8"))[item.recipient];
  assert.ok(proof);
  await page.getByLabel(label("Email confirmation proof", "ای میل تصدیقی کوڈ"), {exact: true}).fill(proof);
  await page.getByRole("button", {name: label("Confirm email", "ای میل کی تصدیق"), exact: true}).click();
  await page.getByLabel(label("Choose your password", "اپنا پاس ورڈ منتخب کریں"), {exact: true}).fill(fixture.password);
  await page.getByLabel(label("Repeat your password", "پاس ورڈ دوبارہ درج کریں"), {exact: true}).fill(fixture.password);
  await page.getByRole("button", {name: label("Set up authenticator", "آتھنٹیکیٹر ترتیب دیں"), exact: true}).click();
  const key = await page.getByLabel(label("Authenticator setup key", "آتھنٹیکیٹر کی کلید"), {exact: true}).inputValue();
  await page.addScriptTag({content: axe.source});
  assert.deepEqual(await page.evaluate(async () => (await window.axe.run(document, {runOnly: {type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"]}})).violations.map(v => v.id)), []);
  await page.getByLabel(label("Authenticator code", "آتھنٹیکیٹر کوڈ"), {exact: true}).fill(totp(key, 0));
  await page.getByRole("button", {name: label("Activate and complete enrollment", "فعال کریں اور اندراج مکمل کریں"), exact: true}).click();
  await page.getByText(label("Personal account and MFA are ready", "ذاتی اکاؤنٹ اور ایم ایف اے تیار ہیں"), {exact: true}).waitFor();
  assert.equal(await page.locator("code").count(), 10);
  assert.equal((await context.cookies()).some(c => c.name === "__Host-pwc_session"), false);
  assert.deepEqual(await page.evaluate(() => ({local: Object.keys(localStorage), session: Object.keys(sessionStorage)})), {local: [], session: []});
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.getByRole("button", {name: label("Clear recovery codes", "بحالی کوڈ ہٹا دیں"), exact: true}).click();
  assert.equal(await page.locator("code").count(), 0);
  await page.goto(`https://ngo.pwc.invalid:${fixture.port}/`);
  await page.getByLabel("Email", {exact: true}).fill(item.recipient);
  await page.getByLabel("Password", {exact: true}).fill(fixture.password);
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await page.getByText("Second factor required. This is not an authenticated session.", {exact: true}).waitFor();
  await page.getByLabel("Second factor code", {exact: true}).fill(totp(key));
  await page.getByRole("button", {name: "Confirm second factor", exact: true}).click();
  await page.getByText("Personal session checked. No active NGO authority.", {exact: true}).waitFor();
  await page.getByRole("button", {name: "Sign out", exact: true}).click();
  await page.getByText("Signed out on the server. Private data cleared.", {exact: true}).waitFor();
}
try {
  for (const [index, item] of fixture.invitations.entries()) await invitationCeremony(item, index ? "ur" : "en");
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
  await wrong.addCookies((await owner.context().cookies()).filter(c => c.name === "__Host-pwc_session").map(c => ({name: c.name, value: c.value, secure: c.secure, httpOnly: c.httpOnly, sameSite: c.sameSite, url: `https://ops.pwc.invalid:${fixture.port}/`})));
  const wrongPage = await wrong.newPage();
  await wrongPage.goto(`https://ops.pwc.invalid:${fixture.port}/`);
  const wrongStatus = await wrongPage.evaluate(async () => (await fetch("/api/v1/auth/me/")).status);
  assert.equal(wrongStatus, 401);
  const wrongReverse = await browser.newContext({ignoreHTTPSErrors: true}); contexts.push(wrongReverse);
  await wrongReverse.addCookies((await ops.context().cookies()).filter(c => c.name === "__Host-pwc_session").map(c => ({name: c.name, value: c.value, secure: c.secure, httpOnly: c.httpOnly, sameSite: c.sameSite, url: `https://ngo.pwc.invalid:${fixture.port}/`})));
  const reversePage = await wrongReverse.newPage(); await reversePage.goto(`https://ngo.pwc.invalid:${fixture.port}/`);
  assert.equal(await reversePage.evaluate(async () => (await fetch("/api/v1/auth/me/")).status), 401);

  await owner.getByRole("button", {name: "Sign out", exact: true}).click();
  await owner.getByText("Signed out on the server. Private data cleared.", {exact: true}).waitFor();
  assert.equal(await owner.getByText("Synthetic Welfare", {exact: true}).count(), 0);
  await owner.getByRole("button", {name: "Check personal session", exact: true}).click();
  await owner.getByText(/Session unavailable or expired/).waitFor();
  const secondFactor = await portal("mfa");
  await secondFactor.getByRole("button", {name: "Sign out", exact: true}).click();
  await secondFactor.getByText("Signed out on the server. Private data cleared.", {exact: true}).waitFor();
  await signIn(secondFactor, "mfa", true);
  assert.equal(await secondFactor.getByRole("button", {name: "Refresh history"}).isDisabled(), true);
  for (const [reason, cookies] of Object.entries(fixture.negatives)) {
    const context = await browser.newContext({ignoreHTTPSErrors: true}); contexts.push(context);
    await context.addCookies(cookies);
    const page = await context.newPage(); await page.goto(`https://ngo.pwc.invalid:${fixture.port}/`);
    await page.getByRole("button", {name: "Check personal session", exact: true}).click();
    await page.getByText(/Session unavailable or expired/).waitFor();
    const status = await page.evaluate(async () => (await fetch("/api/v1/registry/workspace/")).status);
    assert.equal(status, 401, reason);
    assert.equal(await page.getByRole("button", {name: "Refresh history"}).isDisabled(), true);
  }
  // These are actual TLS HTTP transport negatives (Host is forbidden in DOM fetch).
  const spoof = await tlsRequest(foreign, "/api/v1/auth/me/", {"X-Forwarded-Host": "ops.pwc.invalid", "X-Forwarded-Proto": "http", "Forwarded": "proto=http;host=ops.pwc.invalid", "X-Forwarded-For": "203.0.113.18"});
  assert.equal(spoof, 200); // actual TLS/canonical Host, not spoofed claims
  const unknownHost = await tlsRequest(foreign, "/api/v1/auth/me/", {Host: "unlisted.invalid"});
  assert.equal(unknownHost, 400);
  const validCsrf = await foreign.evaluate(async () => (await (await fetch("/api/v1/auth/csrf/")).json()).csrf_token);
  const crossOrigin = await tlsRequest(foreign, "/api/v1/auth/logout/", {Origin: `https://ops.pwc.invalid:${fixture.port}`, "X-CSRFToken": validCsrf, "Content-Type": "application/json", "Content-Length": "0"}, "POST");
  assert.equal(crossOrigin, 403);
  const mixed = await foreign.evaluate(async () => (await fetch("/api/v1/auth/me/", {headers: {Authorization: "Bearer synthetic-not-a-token"}})).status);
  assert.equal(mixed, 400);
  console.log("Actual direct-TLS browser assertions passed: EN/UR invitation email/password/TOTP completion and once-only recovery codes, real password/TOTP/recovery login, cookie/storage controls, anonymous/revoked/expired/inactive, Host/Origin/forwarded-header negatives, both public portals, policy, owner/foreign, filtered lost-response reconciliation, revision/stale, duplicate conflict, CSRF denial. Synthetic certificates/identities only.");
} finally {
  for (const context of contexts) await context.close();
  await browser.close();
}
