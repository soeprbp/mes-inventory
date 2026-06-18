"use server";

import { redirect } from "next/navigation";
import { clearSession, createSession, verifyPasscode } from "@/lib/auth";

export type LoginState = {
  error?: string;
};

export async function loginAction(
  _previousState: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const passcode = String(formData.get("passcode") ?? "");
  const ok = await verifyPasscode(passcode);

  if (!ok) {
    return { error: "Passcode was not accepted." };
  }

  await createSession();
  redirect("/");
}

export async function logoutAction() {
  await clearSession();
  redirect("/");
}
