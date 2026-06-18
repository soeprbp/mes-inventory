"use client";

import { LockKeyhole, LogIn } from "lucide-react";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { loginAction, type LoginState } from "@/app/actions";

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button
      className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-500"
      disabled={pending}
      type="submit"
    >
      <LogIn aria-hidden="true" className="h-4 w-4" />
      {pending ? "Checking" : "Sign in"}
    </button>
  );
}

export function LoginForm() {
  const [state, formAction] = useActionState<LoginState, FormData>(
    loginAction,
    {},
  );

  return (
    <form action={formAction} className="space-y-4">
      <label className="block">
        <span className="mb-2 flex items-center gap-2 text-sm font-medium text-zinc-700">
          <LockKeyhole aria-hidden="true" className="h-4 w-4" />
          Passcode
        </span>
        <input
          autoComplete="current-password"
          className="h-11 w-full rounded-md border border-zinc-300 bg-white px-3 text-base outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
          name="passcode"
          required
          type="password"
        />
      </label>
      {state.error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {state.error}
        </p>
      ) : null}
      <SubmitButton />
    </form>
  );
}
