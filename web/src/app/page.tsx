import { CaptureWorkspace } from "@/components/capture-workspace";
import { LoginForm } from "@/components/login-form";
import { getRecentAssets } from "@/lib/assets";
import { getSession } from "@/lib/auth";
import { getRuntimeStatus } from "@/lib/runtime-status";

export default async function Home() {
  const session = await getSession();

  if (!session) {
    return (
      <main className="min-h-dvh bg-stone-100 text-zinc-950">
        <section className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center px-5 py-8">
          <div className="rounded-md border border-zinc-300 bg-white p-5 shadow-sm">
            <div className="mb-6">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
                MES Inventory
              </p>
              <h1 className="mt-2 text-2xl font-semibold">Field capture</h1>
            </div>
            <LoginForm />
          </div>
        </section>
      </main>
    );
  }

  const [status, assets] = await Promise.all([
    getRuntimeStatus(),
    getRecentAssets(),
  ]);

  return <CaptureWorkspace assets={assets} status={status} />;
}
