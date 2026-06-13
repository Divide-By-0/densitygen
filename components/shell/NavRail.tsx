"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/intake", icon: "▤", label: "Intake" },
  { href: "/candidates", icon: "▦", label: "Candidates" },
  { href: "/trade-offs", icon: "◆", label: "Trade-offs" },
  { href: "/compute", icon: "◷", label: "Compute" },
  { href: "/material", icon: "⬢", label: "Material" },
  { href: "/surface", icon: "⌬", label: "Surface" },
];

export function NavRail() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-shrink-0 basis-[66px] flex-col border-r border-hair bg-canvas pt-1.5">
      {ITEMS.map((it) => {
        const active = pathname.startsWith(it.href);
        return (
          <Link
            key={it.href}
            href={it.href}
            className="flex w-full cursor-pointer flex-col items-center gap-1 px-1 py-[11px]"
            style={{
              background: active ? "var(--color-amber-tint)" : "transparent",
              boxShadow: active ? "inset 2px 0 0 var(--color-amber)" : "none",
              color: active ? "var(--color-amber-deep)" : "var(--color-muted)",
            }}
          >
            <span className="text-[17px] leading-none">{it.icon}</span>
            <span
              className="text-[9.5px] uppercase tracking-[0.04em]"
              style={{ fontWeight: active ? 600 : 500 }}
            >
              {it.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
