import { NextRequest, NextResponse } from "next/server";

import {
  SESSION_COOKIE,
  authConfigError,
  authEnabled,
  buildSessionCookie,
  credentialsAreValid,
  sessionCookieOptions
} from "@/lib/auth";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  if (!authEnabled()) {
    return NextResponse.redirect(new URL("/", request.url), { status: 303 });
  }

  if (authConfigError()) {
    return NextResponse.redirect(new URL("/login?error=config", request.url), { status: 303 });
  }

  const form = await request.formData();
  const username = String(form.get("username") ?? "").trim();
  const password = String(form.get("password") ?? "");

  if (!credentialsAreValid(username, password)) {
    return NextResponse.redirect(new URL("/login?error=invalid", request.url), { status: 303 });
  }

  const response = NextResponse.redirect(new URL("/", request.url), { status: 303 });
  response.cookies.set(SESSION_COOKIE, buildSessionCookie(username), sessionCookieOptions());
  return response;
}
