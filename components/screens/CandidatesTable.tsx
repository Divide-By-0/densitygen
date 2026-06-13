"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { Candidate } from "@/lib/types";
import { sub, fmtHull, fmtKappa } from "@/lib/format";

type Key =
  | "formula"
  | "eform"
  | "eg"
  | "ehull"
  | "K"
  | "kappa"
  | "nsites"
  | "density"
  | "score";

const dotColor = (pass: boolean) => (pass ? "var(--color-ok)" : "var(--color-line)");

export function CandidatesTable({ rows }: { rows: Candidate[] }) {
  const router = useRouter();
  const [sortKey, setSortKey] = useState<Key>("score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const x = a[sortKey];
      const y = b[sortKey];
      if (typeof x === "string" && typeof y === "string") {
        return sortDir === "asc" ? x.localeCompare(y) : y.localeCompare(x);
      }
      const xn = x == null ? -Infinity : (x as number);
      const yn = y == null ? -Infinity : (y as number);
      return sortDir === "asc" ? xn - yn : yn - xn;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const toggle = (k: Key) => {
    if (sortKey === k) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(k);
      setSortDir(k === "formula" ? "asc" : "desc");
    }
  };
  const ind = (k: Key) => (sortKey === k ? (sortDir === "asc" ? " ↑" : " ↓") : "");

  // plain render helper (not a component) — header cell with optional sort
  const th = (label: string, k?: Key, right?: boolean) => (
    <th
      key={label}
      onClick={k ? () => toggle(k) : undefined}
      className={right ? "!text-right" : "!text-left"}
      style={{ cursor: k ? "pointer" : "default" }}
    >
      {label}
      {k ? ind(k) : ""}
    </th>
  );

  return (
    <div className="overflow-auto rounded-[2px] border border-hair bg-surface">
      <table className="dg-table min-w-[1180px]">
        <thead>
          <tr>
            <th className="!text-right">#</th>
            {th("Formula", "formula")}
            {th("MP-ID")}
            {th("System · SPG")}
            {th("E_form", "eform", true)}
            {th("E_g", "eg", true)}
            {th("e_hull", "ehull", true)}
            {th("K", "K", true)}
            {th("κ", "kappa", true)}
            {th("n", "nsites", true)}
            {th("ρ", "density", true)}
            {th("ALD precursor")}
            <th className="!text-center">κ·E_g·H</th>
            {th("Fit", "score")}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr
              key={r.id}
              onClick={() => router.push(`/material/${r.id}`)}
              className="cursor-pointer hover:bg-amber-tint/40"
            >
              <td className="mono !text-right text-faint">{r.rank}</td>
              <td>
                <span className="text-[13px] font-semibold text-ink">{sub(r.formula)}</span>
                {r.front && (
                  <span className="mono ml-[7px] rounded-[2px] border border-amber-border bg-amber-tint px-1 py-px text-[9px] tracking-[0.04em] text-amber-deep">
                    PF
                  </span>
                )}
              </td>
              <td className="mono text-[11.5px] text-muted">{r.id}</td>
              <td className="text-[11.5px] text-muted">
                {r.sys} · <span className="mono">{r.spg}</span>
              </td>
              <td className="mono !text-right text-ink2">{r.eform.toFixed(2)}</td>
              <td className="mono !text-right font-medium text-ink">{r.eg.toFixed(2)}</td>
              <td className="mono !text-right" style={{ color: hullColor(r.ehull) }}>
                {fmtHull(r.ehull)}
              </td>
              <td className="mono !text-right text-ink2">{r.K ?? "—"}</td>
              <td className="mono !text-right font-medium text-ink">{fmtKappa(r.kappa)}</td>
              <td className="mono !text-right text-faint">{r.nsites}</td>
              <td className="mono !text-right text-muted">{r.density.toFixed(2)}</td>
              <td className="mono text-[11.5px] text-muted">{r.ald}</td>
              <td>
                <div className="flex justify-center gap-[3px]">
                  <Dot on={!!r.passK} />
                  <Dot on={!!r.passEg} />
                  <Dot on={!!r.passHull} />
                </div>
              </td>
              <td>
                <div className="flex items-center gap-2">
                  <div className="h-[5px] min-w-[42px] flex-1 overflow-hidden rounded-[2px] bg-hair2">
                    <div className="h-full bg-amber" style={{ width: `${r.score}%` }} />
                  </div>
                  <span className="mono text-[11.5px] font-medium text-ink">{r.score}</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Dot({ on }: { on: boolean }) {
  return <span className="h-[7px] w-[7px] rounded-full" style={{ background: dotColor(on) }} />;
}

const hullColor = (mev: number) =>
  mev === 0 ? "var(--color-ok)" : mev <= 25 ? "var(--color-warn)" : "var(--color-danger)";
