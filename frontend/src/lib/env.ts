import "server-only";

import nextEnv from "@next/env";
import fs from "node:fs";
import path from "node:path";

const { loadEnvConfig } = nextEnv;
const demoAuthConfigured = Boolean(
  process.env.DASHBOARD_DEMO_USER?.trim() && process.env.DASHBOARD_DEMO_PASSWORD?.trim()
);

loadEnvConfig(resolveRootEnvDir(), process.env.NODE_ENV !== "production", console, !demoAuthConfigured);

function resolveRootEnvDir(): string {
  const cwd = process.cwd();
  const candidates = [cwd, path.resolve(cwd, "..")];

  return candidates.find(isProjectRoot) ?? path.resolve(cwd, "..");
}

function isProjectRoot(dir: string): boolean {
  return fs.existsSync(path.join(dir, ".env")) && fs.existsSync(path.join(dir, "frontend", "package.json"));
}
