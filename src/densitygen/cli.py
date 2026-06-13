"""`ald-screen` command-line interface.

Examples:
    ald-screen run examples/wf6_w.json
    ald-screen run examples/wf6_w.json --json
    ald-screen run examples/new_material_screen.json --csv out.csv --uma
    ald-screen recipes        # list the known-good calibration recipes
    ald-screen demo           # run the WF6 -> W headline case
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from densitygen.data import KNOWN_RECIPES
from densitygen.design import design
from densitygen.reporting import render_csv, render_report
from densitygen.schemas import Candidate, ScreeningRequest
from densitygen.screen import screen


def _run(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.request).read_text())
    if args.uma:
        payload["use_ml_potential"] = True
    request = ScreeningRequest.model_validate(payload)
    resp = screen(request)

    if args.csv:
        Path(args.csv).write_text(render_csv(resp))
        print(f"wrote {args.csv}", file=sys.stderr)
    if args.json:
        print(resp.model_dump_json(indent=2))
    else:
        print(render_report(resp))
    return 0


def _recipes(_args: argparse.Namespace) -> int:
    print("Known-good ALD recipes (calibration / regression set):\n")
    for r in KNOWN_RECIPES:
        print(f"  {r.precursor:<8} + {r.co_reactant:<6} -> {r.film:<6}  {r.note}")
    return 0


def _demo(args: argparse.Namespace) -> int:
    # The headline test case the platform is built around: WF6 -> W, screened
    # against a couple of foils so the ranking behavior is visible.
    request = ScreeningRequest(
        film="W",
        co_reactant="B2H6",
        temperature_max_c=350,
        use_ml_potential=args.uma,
        candidates=[
            Candidate(name="WF6"),
            Candidate(name="WCl6", formula="WCl6"),
            Candidate(name="TMA"),  # foil: contains no W, must hard-fail
        ],
    )
    print(render_report(screen(request)))
    return 0


def _viz(args: argparse.Namespace) -> int:
    """Bake the interactive viz bundle from a screening request."""
    from densitygen.viz import response_to_payload, write_bundle

    payload_in = json.loads(Path(args.request).read_text())
    if args.uma:
        payload_in["use_ml_potential"] = True
    request = ScreeningRequest.model_validate(payload_in)
    resp = screen(request)
    data = response_to_payload(resp, request=request, mode="screen")
    entry = write_bundle(data, args.out)
    print(f"wrote viz bundle to {Path(args.out).resolve()}", file=sys.stderr)
    print(f"open: {entry}", file=sys.stderr)
    print(f"  (or run `ald-screen serve {args.request}` for live precursor suggestions)",
          file=sys.stderr)
    return 0


def _serve(args: argparse.Namespace) -> int:
    from densitygen.server import serve

    if args.request:
        payload_in = json.loads(Path(args.request).read_text())
        request = ScreeningRequest.model_validate(payload_in)
    else:
        # A sensible default demo so `ald-screen serve` works with no args.
        request = ScreeningRequest(
            film="HfO2", co_reactant="H2O", temperature_max_c=300,
            forbidden_elements=["Cl"],
            candidates=[
                Candidate(name="TEMAH"), Candidate(name="HfCl4"),
                Candidate(name="TDMAH", formula="Hf[N(CH3)2]4"),
                Candidate(name="Hf(OtBu)4", formula="Hf(OC4H9)4"),
            ],
        )
    serve(request, host=args.host, port=args.port, bundle_dir=args.out)
    return 0


def _design(args: argparse.Namespace) -> int:
    resp = design(
        film=args.film,
        co_reactant=args.co_reactant,
        temperature_max_c=args.temperature_max_c,
        forbidden_elements=[e.strip() for e in (args.forbidden or "").split(",") if e.strip()],
        oxidation=args.oxidation,
        top_n=args.top_n,
        use_ml_potential=args.uma,
    )
    if args.json:
        print(resp.model_dump_json(indent=2))
    else:
        print(render_report(resp))
    return 0


def _interconnects(args: argparse.Namespace) -> int:
    from densitygen.interconnects import (
        HAVE_PRECURSORS, NEED_PRECURSORS, run_design_bucket, run_test_bucket)

    print("=" * 72)
    print("INTERCONNECT RESISTANCE — alternative metals to beat Cu/W at scaled nodes")
    print("=" * 72)
    print("\n### BUCKET A — materials WITH precursors: end-to-end screening tests ###")
    for t in HAVE_PRECURSORS:
        print(f"\n>>> {t.film}: {t.why}")
        print(render_report(run_test_bucket(t, use_ml_potential=args.uma)))
    print("\n\n### BUCKET B — materials WITHOUT precursors: inverse-design demos ###")
    for t in NEED_PRECURSORS:
        print(f"\n>>> {t.film}: {t.why}")
        print(f"    ({t.note})")
        print(render_report(run_design_bucket(t, use_ml_potential=args.uma, top_n=args.top_n)))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ald-screen", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="screen candidates from a JSON request file")
    pr.add_argument("request", help="path to a ScreeningRequest JSON file")
    pr.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    pr.add_argument("--csv", metavar="PATH", help="also write a CSV scorecard")
    pr.add_argument("--uma", action="store_true", help="use the hosted UMA model on Replicate")
    pr.set_defaults(func=_run)

    prc = sub.add_parser("recipes", help="list known-good calibration recipes")
    prc.set_defaults(func=_recipes)

    pd = sub.add_parser("demo", help="run the WF6 -> W headline case")
    pd.add_argument("--uma", action="store_true", help="use the hosted UMA model")
    pd.set_defaults(func=_demo)

    pv = sub.add_parser("viz", help="bake the interactive viz bundle from a request JSON")
    pv.add_argument("request", help="path to a ScreeningRequest JSON file")
    pv.add_argument("--out", default="densitygen_viz", help="output bundle directory")
    pv.add_argument("--uma", action="store_true", help="use the hosted UMA model")
    pv.set_defaults(func=_viz)

    ps = sub.add_parser("serve", help="serve the viz with a live /api/screen for precursor suggestions")
    ps.add_argument("request", nargs="?", default=None,
                    help="optional ScreeningRequest JSON; omitted -> HfO2 demo")
    ps.add_argument("--host", default="127.0.0.1")
    ps.add_argument("--port", type=int, default=8765)
    ps.add_argument("--out", default="densitygen_viz", help="bundle directory to serve")
    ps.set_defaults(func=_serve)

    pg = sub.add_parser("design", help="PROPOSE novel precursors for a film (inverse design)")
    pg.add_argument("--film", required=True, help="target film, e.g. W, Mo, HfO2")
    pg.add_argument("--co-reactant", dest="co_reactant", default=None)
    pg.add_argument("--temperature-max-c", dest="temperature_max_c", type=float, default=None)
    pg.add_argument("--forbidden", default="", help="comma-separated elements to exclude")
    pg.add_argument("--oxidation", type=int, default=None, help="metal oxidation state override")
    pg.add_argument("--top-n", dest="top_n", type=int, default=12)
    pg.add_argument("--uma", action="store_true", help="confirm top survivors with real UMA energies")
    pg.add_argument("--json", action="store_true")
    pg.set_defaults(func=_design)

    pi = sub.add_parser("interconnects",
                        help="interconnect-resistance demo: screen materials with "
                             "precursors, design ones without")
    pi.add_argument("--uma", action="store_true", help="use real ML-potential energies")
    pi.add_argument("--top-n", dest="top_n", type=int, default=6)
    pi.set_defaults(func=_interconnects)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
