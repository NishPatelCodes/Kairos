import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Compass,
  History,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Repeat,
  Settings,
  Target,
} from "lucide-react";
import { useEffect, useState } from "react";

import { clearTokens } from "@/lib/api";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Today", icon: Compass, end: true },
  { to: "/goals", label: "Goals", icon: Target },
  { to: "/progress", label: "Progress", icon: BarChart3 },
  { to: "/habits", label: "Habits", icon: Repeat, soon: true },
  { to: "/history", label: "History", icon: History, soon: true },
  { to: "/settings", label: "Settings", icon: Settings },
];

const NAV_KEY = "kairos.nav-collapsed";

export function AppShell() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(NAV_KEY) === "1");

  useEffect(() => {
    localStorage.setItem(NAV_KEY, collapsed ? "1" : "0");
  }, [collapsed]);

  return (
    <div className="flex h-full bg-bg">
      <aside
        className={cn(
          "flex shrink-0 flex-col border-r border-line py-5 transition-[width] duration-200",
          collapsed ? "w-[72px] items-center px-0" : "w-[72px] items-center lg:w-[220px] lg:items-stretch lg:px-3",
        )}
      >
        <div className={cn("mb-6 flex items-center gap-3", collapsed ? "px-0" : "px-2")}>
          <img
            src="/logo-256.png"
            srcSet="/logo-256.png 256w, /logo.png 2000w"
            sizes="36px"
            alt="Kairos"
            width={36}
            height={36}
            className="h-9 w-9 rounded-lg object-cover"
          />
          {!collapsed && (
            <div className="hidden lg:block">
              <div className="text-[13px] font-medium tracking-[0.18em] text-ink">KAIROS</div>
              <div className="text-[11px] text-ink-faint">Executive OS</div>
            </div>
          )}
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {nav.map((item) => {
            const Icon = item.icon;
            if (item.soon) {
              return (
                <div
                  key={item.to}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-ink-faint/70"
                  title="Coming later"
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span className="hidden text-sm lg:block">{item.label}</span>}
                </div>
              );
            }
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                title={item.label}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-ink-muted transition hover:bg-bg-hover hover:text-ink",
                    isActive && "bg-bg-hover text-ink",
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span className="hidden lg:block">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
        <button
          className="mt-auto flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-ink-faint hover:bg-bg-hover hover:text-ink"
          onClick={() => setCollapsed((value) => !value)}
          title={collapsed ? "Show menu" : "Hide menu"}
        >
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          {!collapsed && <span className="hidden lg:block">Hide menu</span>}
        </button>
        <button
          className="mt-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-ink-faint hover:bg-bg-hover hover:text-ink"
          onClick={() => {
            clearTokens();
            navigate("/login");
          }}
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span className="hidden lg:block">Sign out</span>}
        </button>
      </aside>
      <main className="min-w-0 flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
