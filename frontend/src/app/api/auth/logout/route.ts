import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/auth";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  return clearAndRedirect(request);
}

export async function GET(request: NextRequest) {
  return clearAndRedirect(request);
}

function clearAndRedirect(request: NextRequest) {
  const response = NextResponse.redirect(new URL("/login", request.url), { status: 303 });
  response.cookies.set(SESSION_COOKIE, "", {
    ...sessionCookieOptions(),
    maxAge: 0
  });
  return response;
}
