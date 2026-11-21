import { LogIn } from "lucide-react";
import { loginUrl } from "@/lib/api";

export function SignInScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <section className="panel glow animate-rise w-full max-w-sm p-8 text-center">
        <p className="eyebrow">job hunt telemetry</p>
        <h1 className="mt-1 text-4xl font-bold tracking-tight">
          Pipeline<span className="text-primary">.</span>
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">Sign in to see your dashboard.</p>
        <a
          href={loginUrl()}
          className="mt-6 inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          <LogIn className="h-4 w-4" />
          Sign in with Google
        </a>
      </section>
    </main>
  );
}
