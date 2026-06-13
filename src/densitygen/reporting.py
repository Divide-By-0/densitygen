"""Render screening results for humans (text report) and machines (CSV)."""

from __future__ import annotations

import csv
import io

from densitygen.schemas import ScreeningResponse

_BAR = "█"


def _bar(score: float, width: int = 10) -> str:
    filled = round(score * width)
    return _BAR * filled + "·" * (width - filled)


def render_report(resp: ScreeningResponse) -> str:
    """A compact, terminal-friendly ranked scorecard."""
    lines: list[str] = []
    lines.append(f"ALD precursor screening — target film: {resp.film}"
                 + (f"  (+ {resp.co_reactant})" if resp.co_reactant else ""))
    lines.append(f"compute backend: {resp.model_provenance.compute_backend}"
                 + (f" [{resp.model_provenance.model_name}]" if resp.model_provenance.model_name else ""))
    lines.append("=" * 72)

    for i, c in enumerate(resp.ranked_candidates, 1):
        tag = "  ★ known recipe" if c.is_known_recipe else ""
        if c.origin == "proposed":
            tag += "  ⚗ proposed (novel)"
        lines.append(f"\n#{i}  {c.name}{tag}")
        meta = f"    formula={c.formula or '?'}  MW={c.molecular_weight or '?'}  delivers={c.film_element or '?'}"
        if c.ml_energy_ev is not None:
            meta += f"  UMA E={c.ml_energy_ev:.3f} eV"
        lines.append(meta)
        lines.append(f"    OVERALL  {_bar(c.overall_score)}  {c.overall_score:.2f}")
        for comp in c.components:
            conf = {"measured": "✓", "estimated": "~", "unknown": "?"}.get(comp.confidence, "~")
            lines.append(f"      {comp.name:<19} {_bar(comp.score)} {comp.score:.2f} {conf}  {comp.evidence}")
        for w in c.warnings:
            lines.append(f"    ⚠  {w}")
        lines.append(f"    → {c.recommended_next_step}")

    if resp.warnings:
        lines.append("\nRun warnings:")
        lines.extend(f"  - {w}" for w in resp.warnings)
    lines.append("\nlegend: ✓ measured/literature   ~ estimated   ? unknown")
    return "\n".join(lines)


def render_csv(resp: ScreeningResponse) -> str:
    """Flat CSV: one row per candidate, one column per score component."""
    comp_names = ["delivery", "thermal_window", "surface_reactivity",
                  "self_limiting", "clean_ligand", "byproduct", "integration"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["rank", "name", "formula", "molecular_weight", "film_element",
                "overall_score", *comp_names, "is_known_recipe", "warnings",
                "recommended_next_step"])
    for i, c in enumerate(resp.ranked_candidates, 1):
        by = {comp.name: comp.score for comp in c.components}
        w.writerow([i, c.name, c.formula or "", c.molecular_weight or "",
                    c.film_element or "", c.overall_score,
                    *[by.get(n, "") for n in comp_names],
                    c.is_known_recipe, " | ".join(c.warnings),
                    c.recommended_next_step])
    return buf.getvalue()
