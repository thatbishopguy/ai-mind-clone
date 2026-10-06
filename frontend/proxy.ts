import { createHash, timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

function equal(value: string, expected: string): boolean {
  const digest = (text: string) => createHash("sha256").update(text).digest();
  return timingSafeEqual(digest(value), digest(expected));
}

export function proxy(request: NextRequest) {
  const username = process.env.OWNER_USERNAME;
  const password = process.env.OWNER_PASSWORD;
  if (!username || !password) {
    if (process.env.NODE_ENV === "development" && !username && !password) {
      return NextResponse.next();
    }
    return new NextResponse("Private access is not configured", { status: 503 });
  }
  const header = request.headers.get("authorization") ?? "";
  let user = "", pass = "";
  if (header.startsWith("Basic ")) {
    const decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
    const separator = decoded.indexOf(":");
    if (separator >= 0) {
      user = decoded.slice(0, separator);
      pass = decoded.slice(separator + 1);
    }
  }
  const validUser = equal(user, username);
  const validPassword = equal(pass, password);
  if (!validUser || !validPassword) {
    return new NextResponse("Sign in required", {
      status: 401,
      headers: { "WWW-Authenticate": 'Basic realm="AI Mind Clone"', "Cache-Control": "no-store" },
    });
  }
  const response = NextResponse.next();
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
