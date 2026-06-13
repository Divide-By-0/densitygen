"""End-to-end screening: ScreeningRequest -> ScreeningResponse.

This is the orchestrator a chemist actually calls. It resolves each candidate
to a composition, pulls in any curated literature data, runs the seven score
components (optionally upgraded with real UMA energies), enforces the hard
gates, ranks, and attaches a recommended next computation/experiment.
"""

from __future__ import annotations

from densitygen.chem import Composition, FormulaError, to_composition
from densitygen.compute import EnergyResult, get_backend
from densitygen.data import (
    KNOWN_RECIPES,
    Film,
    KnownPrecursor,
    lookup_film,
    lookup_precursor,
)
from densitygen.scoring import (
    aggregate,
    evaluate_gates,
    score_byproduct,
    score_clean_ligand,
    score_delivery,
    score_self_limiting,
    score_surface_reactivity,
    score_thermal_window,
)
from densitygen.schemas import (
    Candidate,
    CandidateResult,
    ModelProvenance,
    ScoreComponent,
    ScreeningRequest,
    ScreeningResponse,
)


def infer_ligand_class(comp: Composition, film_element: str | None) -> str:
    """Best-effort ligand classification when the precursor isn't in the DB."""
    halo = bool(comp.halogens)
    has_c = comp.count("C") > 0
    has_n = comp.count("N") > 0
    has_o = comp.count("O") > 0
    if halo and not has_c:
        return "halide"
    if has_n and has_c:
        return "alkylamide"
    if has_o and has_c:
        return "alkoxide"
    if has_c:
        return "alkyl"
    if comp.count("H") and comp.n_heavy_atoms <= 2:
        return "hydride"
    return "unknown"


def _is_known_recipe(film: str, precursor_name: str) -> bool:
    pn = precursor_name.strip().lower()
    return any(
        r.film.lower() == film.strip().lower() and r.precursor.lower() == pn
        for r in KNOWN_RECIPES
    )


def _next_step(result_score: float, has_measured: bool, used_uma: bool, hard_fail: bool) -> str:
    if hard_fail:
        return "Reject: cannot deliver the target film element. No computation warranted."
    if result_score >= 0.7 and not used_uma:
        return ("Promote: run UMA adsorption-energy (oc20) on the hydroxylated "
                "target surface to confirm chemisorption, then a single DFT check.")
    if result_score >= 0.7 and used_uma:
        return "Promote to experiment: strong on all axes incl. UMA energetics. Synthesize/trial."
    if result_score >= 0.45:
        return ("Borderline: run UMA on the weakest component before committing "
                "GPU/DFT budget; consider a co-reactant swap.")
    return "Deprioritize: fails multiple ALD constraints; not worth compute budget."


def _resolve_candidate(cand: Candidate) -> tuple[Composition, KnownPrecursor | None]:
    known = lookup_precursor(cand.name) if cand.name else None
    if known is None and cand.formula is None and cand.smiles is None:
        # name didn't resolve and no structure given
        raise FormulaError(
            f"'{cand.name}' is not a known precursor and no formula/SMILES was provided."
        )
    if known is not None:
        comp = to_composition(formula=cand.formula or known.formula)
        return comp, known
    comp = to_composition(formula=cand.formula, smiles=cand.smiles)
    return comp, None


def resolve_film(name: str) -> tuple[Film, list[str]]:
    film = lookup_film(name)
    if film is not None:
        return film, []
    stub = Film(
        formula=name, name=name, film_element=name.rstrip("0123456789"),
        kind="unknown", role="user-specified", typical_coreactants=(),
        notes="Film not in reference DB; scoring proceeds with reduced context.",
    )
    return stub, [f"Film '{name}' not in reference DB; using a best-effort stub."]


def compute_uma_signals(name: str, comp: Composition, film: Film, backend):
    """Run real UMA on a candidate where we can build its geometry.

    Returns (molecular_energy_eV, adsorption_EnergyResult, notes). Anything we
    can't build (polyatomic-ligand organometallics, unknown lattices) comes back
    None so the caller transparently falls back to descriptors for that axis.
    """
    from densitygen import structures as S

    notes: list[str] = []
    mol = S.build_molecule(name, comp)
    if mol is None:
        return None, None, [f"{name}: no 3D geometry builder (descriptor fallback)"]

    is_local = hasattr(backend, "energy_atoms")
    # (1) Molecular energy (omol) -- a real number that proves UMA ran and feeds
    # stability reasoning.
    if is_local:
        mol_e = backend.energy_atoms(mol, task="omol").energy_ev
    else:
        mol_e = backend.energy(S.to_extxyz(mol), task="omol").energy_ev

    # (2) Adsorption energy (oc20) on the film surface -- only meaningful when we
    # have a real slab. For metal films the elemental slab IS the film; for
    # oxides it would be an elemental-metal proxy, so we skip those for honesty.
    ads: EnergyResult | None = None
    if film.kind == "metal":
        slab = S.build_metal_slab(film.film_element, size=(2, 2, 2))
        if slab is not None:
            system = S.build_adsorption_system(slab, mol)
            if is_local:
                ads = backend.adsorption_energy_atoms(system=system, slab=slab, molecule=mol)
            else:
                ads = backend.adsorption_energy(
                    system_xyz=S.to_extxyz(system), slab_xyz=S.to_extxyz(slab),
                    molecule_xyz=S.to_extxyz(mol))
        else:
            notes.append(f"{name}: no slab builder for {film.film_element}")
    return mol_e, ads, notes


def build_scorecard(*, name: str, comp: Composition, known, film: Film,
                    co_reactant, temperature_max_c, forbidden_elements,
                    ads_energy: EnergyResult | None = None, ml_energy_ev=None,
                    used_uma: bool = False, origin: str = "input",
                    is_known: bool = False) -> CandidateResult:
    """Assemble one candidate's full scorecard. Shared by screen() and design()."""
    ligand_class = known.ligand_class if known and known.ligand_class else \
        infer_ligand_class(comp, film.film_element)

    comps: list[ScoreComponent] = [
        score_delivery(comp, known),
        score_thermal_window(comp, known, temperature_max_c, ligand_class),
        score_surface_reactivity(film, co_reactant, ligand_class, ads_energy),
        score_self_limiting(comp, ligand_class),
        score_clean_ligand(comp, ligand_class),
        score_byproduct(comp, co_reactant, ligand_class),
    ]
    integration_score, gate_warnings = evaluate_gates(comp, film, forbidden_elements)
    comps.append(ScoreComponent(
        name="integration", score=integration_score,
        evidence=(gate_warnings[0] if gate_warnings else
                  f"Delivers {film.film_element}; no forbidden elements."),
        confidence="measured" if known else "estimated",
    ))

    hard_fail = any("HARD FAIL" in w for w in gate_warnings)
    overall = aggregate(comps, integration_score, hard_fail)
    warnings = list(gate_warnings)
    if known and known.hazards:
        warnings.append("Hazards: " + ", ".join(known.hazards))
    has_measured = any(c.confidence == "measured" for c in comps)

    return CandidateResult(
        name=name,
        formula=(comp.formula_input or (known.formula if known else None)),
        molecular_weight=comp.molecular_weight,
        film_element=comp.film_element(prefer=film.film_element),
        overall_score=overall,
        components=comps,
        warnings=warnings,
        recommended_next_step=_next_step(overall, has_measured, used_uma, hard_fail),
        is_known_recipe=is_known,
        origin=origin,
        ml_energy_ev=ml_energy_ev,
    )


def screen(request: ScreeningRequest, backend=None) -> ScreeningResponse:
    film, response_warnings = resolve_film(request.film)

    if request.use_ml_potential and backend is None:
        backend = get_backend()
    # REASON: `any_used_uma` is a run-level flag for provenance only. The
    # per-candidate `cand_used_uma` below is what drives each scorecard's
    # recommended_next_step -- otherwise one candidate's successful UMA run
    # would leak into later candidates' next-step text ("incl. UMA energetics")
    # even though UMA never ran on them.
    any_used_uma = False
    if request.use_ml_potential and backend is None:
        response_warnings.append(
            "use_ml_potential requested but no UMA backend reachable (need local "
            "fairchem-core + HF_TOKEN, or a deployed Replicate model); fell back "
            "to descriptor scoring."
        )

    results: list[CandidateResult] = []
    for cand in request.candidates:
        try:
            comp, known = _resolve_candidate(cand)
        except (FormulaError, ValueError) as e:
            results.append(CandidateResult(
                name=cand.name, overall_score=0.0, components=[],
                warnings=[f"Could not evaluate: {e}"],
                recommended_next_step="Provide a valid molecular formula or SMILES."))
            continue

        ads_energy = None
        ml_energy = None
        cand_used_uma = False
        if request.use_ml_potential and backend is not None:
            try:
                ml_energy, ads_energy, notes = compute_uma_signals(cand.name, comp, film, backend)
                if ml_energy is not None or ads_energy is not None:
                    cand_used_uma = True
                    any_used_uma = True
                response_warnings.extend(notes)
            except Exception as e:  # UMA failure must never crash the screen
                response_warnings.append(f"{cand.name}: UMA compute failed ({e}); used descriptors.")

        results.append(build_scorecard(
            name=cand.name, comp=comp, known=known, film=film,
            co_reactant=request.co_reactant, temperature_max_c=request.temperature_max_c,
            forbidden_elements=request.forbidden_elements,
            ads_energy=ads_energy, ml_energy_ev=ml_energy, used_uma=cand_used_uma,
            origin="input", is_known=_is_known_recipe(request.film, cand.name)))

    results.sort(key=lambda r: r.overall_score, reverse=True)
    return ScreeningResponse(
        film=request.film, co_reactant=request.co_reactant,
        ranked_candidates=results, warnings=response_warnings,
        model_provenance=_provenance(any_used_uma, backend))


_BACKEND_LABEL = {"LocalUMA": "uma-local", "LocalMACE": "mace-local",
                  "LocalCHGNet": "chgnet-local", "MLPotentialClient": "uma-replicate"}


def _provenance(used_uma: bool, backend) -> ModelProvenance:
    if used_uma and backend is not None:
        label = _BACKEND_LABEL.get(type(backend).__name__, "ml-potential")
        is_remote = type(backend).__name__ == "MLPotentialClient"
        return ModelProvenance(
            compute_backend=label,
            model_name=getattr(backend, "model", None),
            replicate_model=getattr(backend, "model", None) if is_remote else None,
            notes="Real ML-potential energies computed where geometry was buildable; "
                  "descriptors elsewhere. Each axis is tagged measured/estimated. "
                  "(UMA is the configured primary; it is gated on HuggingFace, so an "
                  "ungated potential is used here when UMA access is unavailable.)")
    return ModelProvenance(
        compute_backend="local-descriptors",
        notes="Fast descriptor scoring. Pass use_ml_potential=true with "
              "fairchem-core installed (or a deployed Replicate model) for real "
              "UMA atomistic energies.")
