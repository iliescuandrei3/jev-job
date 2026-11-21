import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { PanelState } from "@/components/dashboard/PanelState";
import { AuthContext, useMe } from "@/hooks/use-auth";
import { SignInScreen } from "./SignInScreen";

/** Renders `children` only for a signed-in user; otherwise a skeleton, the sign-in screen or an error. */
export function AuthGate({ children }: { children: ReactNode }) {
  const me = useMe();

  if (me.isPending) return <PageSkeleton />;

  if (me.isError) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <section className="panel w-full max-w-md p-6">
          <PanelState isLoading={false} error={me.error} onRetry={() => void me.refetch()} />
        </section>
      </main>
    );
  }

  if (!me.data) return <SignInScreen />;

  return (
    <AuthContext.Provider value={{ user: me.data.user, csrfToken: me.data.csrf_token }}>
      {children}
    </AuthContext.Provider>
  );
}

function PageSkeleton() {
  return (
    <main aria-busy="true" aria-label="Loading" className="mx-auto max-w-7xl space-y-6 px-4 py-8 md:px-8">
      <div className="space-y-2">
        <Skeleton className="h-3 w-48" />
        <Skeleton className="h-12 w-56" />
      </div>
      <Skeleton className="h-14 w-full rounded-xl" />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-72 rounded-xl lg:col-span-2" />
        <Skeleton className="h-72 rounded-xl" />
      </div>
    </main>
  );
}
