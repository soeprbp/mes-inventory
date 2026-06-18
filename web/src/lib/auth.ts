import "server-only";

import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

const sessionCookieName = "mes_session";
const sessionTtlSeconds = 60 * 60 * 24 * 7;

export type Session = {
  expiresAt: number;
};

function hashPasscode(passcode: string) {
  return createHash("sha256").update(passcode).digest("hex");
}

function safeEqual(left: string, right: string) {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);

  if (leftBuffer.length !== rightBuffer.length) {
    return false;
  }

  return timingSafeEqual(leftBuffer, rightBuffer);
}

function getSessionSecret() {
  return (
    process.env.APP_SESSION_SECRET ??
    process.env.APP_PASSCODE_HASH ??
    "local-development-session-secret"
  );
}

function sign(payload: string) {
  return createHmac("sha256", getSessionSecret()).update(payload).digest("base64url");
}

export async function verifyPasscode(passcode: string) {
  const stored = process.env.APP_PASSCODE_HASH;

  if (!stored || !passcode) {
    return false;
  }

  if (stored.startsWith("plain:")) {
    return safeEqual(passcode, stored.slice("plain:".length));
  }

  const expected = stored.startsWith("sha256:")
    ? stored.slice("sha256:".length)
    : stored;

  return safeEqual(hashPasscode(passcode), expected);
}

export async function createSession() {
  const expiresAt = Date.now() + sessionTtlSeconds * 1000;
  const nonce = randomBytes(12).toString("base64url");
  const payload = Buffer.from(JSON.stringify({ expiresAt, nonce })).toString(
    "base64url",
  );
  const value = `${payload}.${sign(payload)}`;
  const cookieStore = await cookies();

  cookieStore.set(sessionCookieName, value, {
    httpOnly: true,
    maxAge: sessionTtlSeconds,
    path: "/",
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
  });
}

export async function clearSession() {
  const cookieStore = await cookies();
  cookieStore.delete(sessionCookieName);
}

export async function getSession(): Promise<Session | null> {
  const cookieStore = await cookies();
  const raw = cookieStore.get(sessionCookieName)?.value;

  if (!raw) {
    return null;
  }

  const [payload, signature] = raw.split(".");

  if (!payload || !signature || !safeEqual(sign(payload), signature)) {
    return null;
  }

  try {
    const parsed = JSON.parse(
      Buffer.from(payload, "base64url").toString("utf8"),
    ) as Session;

    if (!parsed.expiresAt || parsed.expiresAt <= Date.now()) {
      return null;
    }

    return parsed;
  } catch {
    return null;
  }
}
