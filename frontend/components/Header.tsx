"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getStoredSessionId } from "@/lib/session";

const BASE_NAV = [
  { href: "/", label: "Home", requiresSession: false },
  { href: "/planner", label: "Planner", requiresSession: false },
];

const SESSION_NAV = [
  { segment: "results", label: "Results" },
  { segment: "checklist", label: "Checklist" },
  { segment: "products", label: "Products" },
  { segment: "timeline", label: "Timeline" },
] as const;

export function Header({ sessionId: sessionIdProp }: { sessionId?: string | null }) {
  const pathname = usePathname();
  const [storedSession, setStoredSession] = useState<string | null>(null);

  useEffect(() => {
    setStoredSession(getStoredSessionId());
  }, [sessionIdProp, pathname]);

  const sessionId = sessionIdProp ?? storedSession;

  function isActive(href: string): boolean {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-ivory/95 shadow-soft backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <Link
          href="/"
          className="text-lg font-bold tracking-tight text-espresso"
        >
          DormMove <span className="text-brand">AI</span>
        </Link>

        <nav className="flex flex-wrap items-center gap-1 sm:gap-1.5">
          {BASE_NAV.map(({ href, label }) => (
            <NavLink key={href} href={href} active={isActive(href)} label={label} />
          ))}

          {SESSION_NAV.map(({ segment, label }) => {
            const href = sessionId ? `/${segment}/${sessionId}` : "/planner";
            const active = pathname.startsWith(`/${segment}/`);
            if (!sessionId) {
              return (
                <span
                  key={segment}
                  role="link"
                  aria-disabled="true"
                  aria-label={`${label} — start planning to unlock`}
                  title="Start planning to unlock this view"
                  className="cursor-not-allowed rounded-lg px-3 py-2 text-sm text-muted/50"
                >
                  {label}
                </span>
              );
            }
            return (
              <NavLink key={segment} href={href} active={active} label={label} />
            );
          })}
        </nav>
      </div>
    </header>
  );
}

function NavLink({
  href,
  active,
  label,
}: {
  href: string;
  active: boolean;
  label: string;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      aria-label={label}
      className={`rounded-lg px-3 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-brand/30 ${
        active
          ? "bg-brand-light text-brand"
          : "text-muted hover:bg-cream hover:text-espresso"
      }`}
    >
      {label}
    </Link>
  );
}
