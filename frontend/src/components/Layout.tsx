import { NavLink, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/tasks", label: "Tasks", end: false },
  { to: "/focus", label: "Focus", end: false },
  { to: "/matches", label: "Partners", end: false },
  { to: "/rooms", label: "Rooms", end: false },
  { to: "/profile", label: "Profile", end: false },
];

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-5xl px-5 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <span className="font-display text-xl text-growth">StudySync</span>
            <nav className="flex gap-5">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `text-sm transition-colors ${
                      isActive ? "text-ink font-medium" : "text-slate hover:text-ink"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate hidden sm:inline">{user?.name}</span>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="text-sm text-slate hover:text-ink transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>
    </div>
  );
}
