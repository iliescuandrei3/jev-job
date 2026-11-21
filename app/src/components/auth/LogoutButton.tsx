import { LogOut } from "lucide-react";
import { useAuth, useLogout } from "@/hooks/use-auth";

export function LogoutButton() {
  const { user } = useAuth();
  const logout = useLogout();

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="max-w-[200px] truncate text-muted-foreground" title={user.email}>
        {user.name ?? user.email}
      </span>
      <button
        type="button"
        onClick={() => logout.mutate()}
        disabled={logout.isPending}
        className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition-colors hover:border-primary disabled:opacity-50"
      >
        <LogOut className="h-3.5 w-3.5" />
        {logout.isPending ? "Signing out…" : "Sign out"}
      </button>
      {logout.isError && <span className="text-xs text-destructive">Sign-out failed</span>}
    </div>
  );
}
