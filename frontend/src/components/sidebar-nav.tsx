"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bike,
  Bot,
  Boxes,
  Clock3,
  Home,
  PackageSearch,
  Search,
  ShieldCheck,
  Users
} from "lucide-react";

const navItems = [
  { href: "/", label: "Bảng điều khiển", icon: Home },
  { href: "/sales", label: "Bán hàng", icon: BarChart3 },
  { href: "/products", label: "Sản phẩm", icon: PackageSearch },
  { href: "/inventory", label: "Tồn kho", icon: Boxes },
  { href: "/customers", label: "Khách hàng", icon: Users },
  { href: "/staff", label: "Nhân sự", icon: ShieldCheck },
  { href: "/delivery", label: "Giao hàng", icon: Clock3 },
  { href: "/copilot", label: "Trợ lý AI", icon: Bot }
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <>
      <div className="workspace-card">
        <span>Workspace</span>
        <strong>
          Bike Store
          <em>PRO</em>
        </strong>
      </div>
      <div className="sidebar-search" aria-label="Tìm nhanh">
        <Search aria-hidden="true" />
        <span>Tìm phân tích...</span>
      </div>
      <p className="nav-section-label">Điều hành</p>
      <nav className="nav-list" aria-label="Bảng điều khiển">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link className={`nav-link${active ? " active" : ""}`} href={item.href} key={item.href}>
              <Icon aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}

export function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">
        <Bike size={22} />
      </span>
      <span className="brand-title">
        <strong>Bike Store</strong>
        <span>Trợ lý phân tích</span>
      </span>
    </div>
  );
}
