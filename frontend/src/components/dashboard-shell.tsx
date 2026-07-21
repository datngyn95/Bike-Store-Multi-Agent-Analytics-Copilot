import type { ReactNode } from "react";
import { LogOut } from "lucide-react";

import { DashboardTopbar } from "@/components/dashboard-topbar";
import { Brand, SidebarNav } from "@/components/sidebar-nav";
import type { Session } from "@/lib/auth";

type DashboardShellProps = {
  session: Session;
  children: ReactNode;
};

export function DashboardShell({ session, children }: DashboardShellProps) {
  return (
    <div className="app-stage">
      <div className="app-frame">
        <div className="window-chrome" aria-hidden="true">
          <span className="window-dot red" />
          <span className="window-dot amber" />
          <span className="window-dot green" />
          <span className="window-address">bike-store.analytics</span>
        </div>
        <div className="app-shell">
          <aside className="sidebar">
            <Brand />
            <SidebarNav />
            <div className="sidebar-footer">
              <p className="user-chip">Người dùng: {session.username}</p>
              {session.authEnabled ? (
                <form action="/api/auth/logout" method="post">
                  <button className="logout-button" type="submit" title="Đăng xuất">
                    <LogOut aria-hidden="true" />
                    <span>Đăng xuất</span>
                  </button>
                </form>
              ) : (
                <p className="user-chip">Xác thực: tắt</p>
              )}
            </div>
          </aside>
          <section className="workspace">
            <DashboardTopbar username={session.username} />
            <main className="main">{children}</main>
          </section>
        </div>
      </div>
    </div>
  );
}
