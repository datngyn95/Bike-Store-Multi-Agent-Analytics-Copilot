import "server-only";
import "@/lib/env";

import { createHmac, timingSafeEqual } from "node:crypto";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export const SESSION_COOKIE = "bike_store_demo_session";

const SESSION_MAX_AGE_SECONDS = 60 * 60 * 8;
const DEVELOPMENT_SESSION_SECRET = `dev-${Date.now()}-${Math.random()}`;

type SessionPayload = {
  username: string;
  expiresAt: number;
};

export type Session = {
  username: string;
  authEnabled: boolean;
};

export function authEnabled(): boolean {
  const rawValue = process.env.DASHBOARD_AUTH_ENABLED;
  if (!rawValue) {
    return true;
  }
  return !["0", "false", "no", "off"].includes(rawValue.trim().toLowerCase());
}

export function authConfigError(): string | null {
  if (!authEnabled()) {
    return null;
  }
  if (!expectedUsername() || !expectedPassword()) {
    return "Missing DASHBOARD_DEMO_USER or DASHBOARD_DEMO_PASSWORD.";
  }
  if (!sessionSecret() && process.env.NODE_ENV === "production") {
    return "Missing AUTH_COOKIE_SECRET or JWT_SECRET.";
  }
  return null;
}

export function credentialsAreValid(username: string, password: string): boolean {
  const expectedUser = expectedUsername();
  const expectedPass = expectedPassword();
  return Boolean(expectedUser && expectedPass && username === expectedUser && password === expectedPass);
}

export function buildSessionCookie(username: string): string {
  const secret = sessionSecret();
  if (!secret) {
    throw new Error("Missing AUTH_COOKIE_SECRET or JWT_SECRET.");
  }
  const payload = encodeBase64Url(
    JSON.stringify({
      username,
      expiresAt: Date.now() + SESSION_MAX_AGE_SECONDS * 1000
    } satisfies SessionPayload)
  );
  return `${payload}.${signature(payload, secret)}`;
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: cookieSecure(),
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS
  };
}

export async function readSession(): Promise<Session | null> {
  if (!authEnabled()) {
    return { username: "demo", authEnabled: false };
  }
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (!token) {
    return null;
  }
  const payload = verifySessionCookie(token);
  if (!payload) {
    return null;
  }
  return { username: payload.username, authEnabled: true };
}

export async function requireSession(): Promise<Session> {
  const session = await readSession();
  if (!session) {
    redirect("/login");
  }
  return session;
}

function verifySessionCookie(token: string): SessionPayload | null {
  const [payload, providedSignature] = token.split(".");
  const secret = sessionSecret();
  if (!payload || !providedSignature || !secret) {
    return null;
  }
  const expectedSignature = signature(payload, secret);
  if (!safeEqual(providedSignature, expectedSignature)) {
    return null;
  }
  try {
    const parsed = JSON.parse(decodeBase64Url(payload)) as SessionPayload;
    if (!parsed.username || parsed.expiresAt < Date.now()) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function expectedUsername(): string {
  return process.env.DASHBOARD_DEMO_USER?.trim() || "";
}

function expectedPassword(): string {
  return process.env.DASHBOARD_DEMO_PASSWORD?.trim() || "";
}

function sessionSecret(): string {
  return process.env.AUTH_COOKIE_SECRET?.trim() || process.env.JWT_SECRET?.trim() || DEVELOPMENT_SESSION_SECRET;
}

function cookieSecure(): boolean {
  const rawValue = process.env.AUTH_COOKIE_SECURE?.trim().toLowerCase();
  if (rawValue) {
    return ["1", "true", "yes", "on"].includes(rawValue);
  }
  return process.env.NODE_ENV === "production";
}

function signature(payload: string, secret: string): string {
  return createHmac("sha256", secret).update(payload).digest("base64url");
}

function encodeBase64Url(value: string): string {
  return Buffer.from(value, "utf8").toString("base64url");
}

function decodeBase64Url(value: string): string {
  return Buffer.from(value, "base64url").toString("utf8");
}

function safeEqual(left: string, right: string): boolean {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}
