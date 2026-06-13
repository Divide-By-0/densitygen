"use client";

import { useMemo, useRef, useState } from "react";
import type { MPStructure } from "@/lib/types";
import { projectStructure } from "@/lib/structure-view";

const SIZE = 360;

export function CrystalViewer({ structure }: { structure?: MPStructure }) {
  const [rot, setRot] = useState({ x: 0.4, y: 0.5 });
  const drag = useRef<{ x: number; y: number } | null>(null);

  const scene = useMemo(
    () => (structure ? projectStructure(structure, rot.x, rot.y, SIZE) : null),
    [structure, rot],
  );

  const elements = useMemo(() => {
    if (!structure) return [];
    const seen = new Set<string>();
    const out: { el: string; anion: boolean }[] = [];
    for (const s of structure.sites) {
      if (!seen.has(s.element)) {
        seen.add(s.element);
        out.push({ el: s.element, anion: ["O", "N", "F", "S"].includes(s.element) });
      }
    }
    return out;
  }, [structure]);

  const onDown = (e: React.PointerEvent) => {
    drag.current = { x: e.clientX, y: e.clientY };
    (e.target as Element).setPointerCapture?.(e.pointerId);
  };
  const onMove = (e: React.PointerEvent) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    drag.current = { x: e.clientX, y: e.clientY };
    setRot((r) => ({ x: clamp(r.x + dy * 0.01, -1.3, 1.3), y: r.y + dx * 0.01 }));
  };
  const onUp = () => {
    drag.current = null;
  };

  return (
    <div className="card overflow-hidden">
      <div className="card-head">
        <span>Crystal structure</span>
        <span className="mono text-[10px] text-faint">{structure ? "DRAG TO ROTATE" : "—"}</span>
      </div>
      <div
        className="relative touch-none bg-canvas"
        style={{ cursor: structure ? "grab" : "default" }}
        onPointerDown={onDown}
        onPointerMove={onMove}
        onPointerUp={onUp}
        onPointerLeave={onUp}
      >
        <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="block h-auto w-full">
          <defs>
            <radialGradient id="gCat" cx="35%" cy="32%" r="72%">
              <stop offset="0%" stopColor="#E9A86A" />
              <stop offset="55%" stopColor="#B45309" />
              <stop offset="100%" stopColor="#7A3606" />
            </radialGradient>
            <radialGradient id="gAn" cx="35%" cy="32%" r="72%">
              <stop offset="0%" stopColor="#9AA6B4" />
              <stop offset="55%" stopColor="#334155" />
              <stop offset="100%" stopColor="#1C2530" />
            </radialGradient>
          </defs>
          {scene ? (
            <>
              {scene.bonds.map((b, i) => (
                <line key={i} x1={b.x1} y1={b.y1} x2={b.x2} y2={b.y2} stroke="#C9C6C0" strokeWidth={3} strokeLinecap="round" />
              ))}
              {scene.atoms.map((a, i) => (
                <circle
                  key={i}
                  cx={a.x}
                  cy={a.y}
                  r={a.r}
                  fill={a.anion ? "url(#gAn)" : "url(#gCat)"}
                  stroke="rgba(0,0,0,.15)"
                  strokeWidth={0.5}
                />
              ))}
            </>
          ) : (
            <text x={SIZE / 2} y={SIZE / 2} textAnchor="middle" className="mono" fontSize={11} fill="var(--color-faint)">
              structure unavailable
            </text>
          )}
        </svg>
        {elements.length > 0 && (
          <div className="mono absolute bottom-2.5 left-3 flex gap-3 text-[11px] text-muted">
            {elements.slice(0, 4).map((e) => (
              <span key={e.el}>
                <span
                  className="mr-1 inline-block h-[11px] w-[11px] rounded-full align-[-1px]"
                  style={{ background: e.anion ? "#334155" : "#B45309" }}
                />
                {e.el}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5 border-t border-hair bg-surface px-[13px] py-[9px]">
        {["Ball + stick", "Polyhedra", "Unit cell", "2×2×2", ".cif ↓"].map((t, i) => (
          <span
            key={t}
            className="mono rounded-[2px] px-[9px] py-1 text-[10.5px]"
            style={
              i === 0
                ? { background: "var(--color-ink)", color: "#fff" }
                : { background: "var(--color-panel)", color: "var(--color-muted)", border: "1px solid var(--color-hair)" }
            }
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
