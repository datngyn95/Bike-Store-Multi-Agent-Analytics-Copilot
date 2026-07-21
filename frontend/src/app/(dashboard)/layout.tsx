import { DashboardShell } from "@/components/dashboard-shell";
import { requireSession } from "@/lib/auth";

export default async function ProtectedLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const session = await requireSession();
  return <DashboardShell session={session}>{children}</DashboardShell>;
}
