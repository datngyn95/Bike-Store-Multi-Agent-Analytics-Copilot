"use client";

import { Bell, ChevronRight, Command, Search, ShieldCheck, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";

const pageLabels: Record<string, string> = {
  "/": "Tổng quan",
  "/copilot": "Trợ lý AI",
  "/customers": "Khách hàng",
  "/inventory": "Tồn kho",
  "/products": "Sản phẩm",
  "/sales": "Bán hàng"
};

function currentPage(pathname: string): string {
  const match = Object.keys(pageLabels)
    .filter((path) => (path === "/" ? pathname === "/" : pathname.startsWith(path)))
    .sort((a, b) => b.length - a.length)[0];
  return pageLabels[match ?? "/"];
}

export function DashboardTopbar({ username }: { username: string }) {
  const pathname = usePathname();
  const page = currentPage(pathname);

  return (
    <header className="topbar">
      <div className="breadcrumbs" aria-label="Vị trí">
        <span>Bike Store</span>
        <ChevronRight aria-hidden="true" />
        <strong>{page}</strong>
      </div>

      <div className="top-search" aria-label="Tìm kiếm">
        <Search aria-hidden="true" />
        <span>Tìm KPI, sản phẩm, khách hàng...</span>
        <kbd>
          <Command aria-hidden="true" />
          K
        </kbd>
      </div>

      <div className="topbar-actions">
        <span className="sync-pill">
          <ShieldCheck aria-hidden="true" />
          Dữ liệu sẵn sàng
        </span>
        <button className="icon-button" type="button" title="Thông báo">
          <Bell aria-hidden="true" />
        </button>
        <div className="top-user">
          <span className="user-avatar" aria-hidden="true">
            <Sparkles size={16} />
          </span>
          <span>
            <small>Người dùng</small>
            <strong>{username}</strong>
          </span>
        </div>
      </div>
    </header>
  );
}
