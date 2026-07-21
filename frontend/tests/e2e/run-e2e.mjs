import { spawn, spawnSync } from "node:child_process";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(here, "..", "..");
const isWindows = process.platform === "win32";

const nextCli = path.join(frontendRoot, "node_modules", "next", "dist", "bin", "next");
const playwrightCli = path.join(frontendRoot, "node_modules", "playwright", "cli.js");
const mockApiScript = path.join(frontendRoot, "tests", "e2e", "mock-api-server.mjs");

const mockApiPort = process.env.PLAYWRIGHT_MOCK_API_PORT ?? "8010";
const frontendPort = process.env.PLAYWRIGHT_FRONTEND_PORT ?? "3001";
const apiBaseURL = process.env.PLAYWRIGHT_API_BASE_URL ?? `http://127.0.0.1:${mockApiPort}`;
const frontendBaseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${frontendPort}`;

const e2eEnv = {
  ...process.env,
  API_BASE_URL: apiBaseURL,
  NEXT_PUBLIC_API_BASE_URL: apiBaseURL,
  DASHBOARD_AUTH_ENABLED: "true",
  DASHBOARD_DEMO_USER: process.env.DASHBOARD_DEMO_USER ?? "demo",
  DASHBOARD_DEMO_PASSWORD: process.env.DASHBOARD_DEMO_PASSWORD ?? "demo-password",
  AUTH_COOKIE_SECRET: process.env.AUTH_COOKIE_SECRET ?? "playwright-local-demo-secret",
  AUTH_COOKIE_SECURE: "false",
  PLAYWRIGHT_API_BASE_URL: apiBaseURL,
  PLAYWRIGHT_BASE_URL: frontendBaseURL,
  PLAYWRIGHT_FRONTEND_PORT: frontendPort,
  PLAYWRIGHT_MANAGED_SERVERS: "1",
  PLAYWRIGHT_MOCK_API_PORT: mockApiPort,
  NEXT_TELEMETRY_DISABLED: "1"
};

const children = [];
let exitCode = 1;

try {
  runNode(nextCli, ["build"]);

  children.push(
    startNode("mock-fastapi", mockApiScript, ["--port", mockApiPort]),
    startNode("next-frontend", nextCli, ["start", "--hostname", "127.0.0.1", "--port", frontendPort])
  );

  await waitForUrl(`${apiBaseURL}/health`, 30_000);
  await waitForUrl(frontendBaseURL, 120_000);

  const result = runNode(playwrightCli, ["test", ...process.argv.slice(2)], false);
  exitCode = result.status ?? 1;
} finally {
  stopChildren();
}

process.exit(exitCode);

function runNode(script, args, exitOnFailure = true) {
  const result = spawnSync(process.execPath, [script, ...args], {
    cwd: frontendRoot,
    env: e2eEnv,
    stdio: "inherit"
  });

  if (result.error) {
    console.error(result.error.message);
    if (exitOnFailure) {
      process.exit(1);
    }
  }
  if (exitOnFailure && result.status !== 0) {
    process.exit(result.status ?? 1);
  }
  return result;
}

function startNode(name, script, args) {
  const child = spawn(process.execPath, [script, ...args], {
    cwd: frontendRoot,
    env: e2eEnv,
    stdio: ["ignore", "pipe", "pipe"]
  });

  child.stdout.on("data", (chunk) => process.stdout.write(prefixOutput(name, chunk)));
  child.stderr.on("data", (chunk) => process.stderr.write(prefixOutput(name, chunk)));
  child.on("exit", (code) => {
    if (code !== null && code !== 0) {
      process.stderr.write(`[${name}] exited with code ${code}\n`);
    }
  });

  return child;
}

function prefixOutput(name, chunk) {
  return String(chunk)
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => `[${name}] ${line}\n`)
    .join("");
}

async function waitForUrl(url, timeoutMs) {
  const startedAt = Date.now();
  let lastError = "";

  while (Date.now() - startedAt < timeoutMs) {
    try {
      const statusCode = await getStatus(url);
      if (statusCode >= 200 && statusCode < 500) {
        return;
      }
      lastError = `status ${statusCode}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await delay(500);
  }

  throw new Error(`Timed out waiting for ${url}: ${lastError}`);
}

function getStatus(url) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, { timeout: 2_000 }, (response) => {
      response.resume();
      response.on("end", () => resolve(response.statusCode ?? 0));
    });
    request.on("timeout", () => {
      request.destroy(new Error("request timed out"));
    });
    request.on("error", reject);
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stopChildren() {
  for (const child of children.reverse()) {
    if (!child.pid || child.killed) {
      continue;
    }

    if (isWindows) {
      spawnSync("taskkill.exe", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
    } else {
      child.kill("SIGTERM");
    }
  }
}
