"""Curated reference data for known ALD precursors and co-reactants.

Values are pulled from the ALD literature and vendor datasheets. They are the
*ground truth* the screener calibrates against: a model that can't rank these
known-good precursors correctly should not be trusted on novel ones.

Each entry separates measured/literature facts (boiling point, decomposition
temperature, known process window) from things the screener will estimate, so
provenance stays honest. Where a value is genuinely unknown we leave it None
rather than inventing a number.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnownPrecursor:
    name: str
    aliases: tuple[str, ...]
    formula: str
    film_element: str
    # Literature delivery data (None == not well established / not found).
    vapor_pressure_note: str | None = None
    bubbler_temp_c: float | None = None          # typical source/bubbler temperature
    decomposition_onset_c: float | None = None    # self-decomposition onset
    ald_window_c: tuple[float, float] | None = None  # demonstrated self-limiting window
    common_coreactants: tuple[str, ...] = ()
    ligand_class: str = ""                         # halide | alkyl | alkylamide | etc.
    hazards: tuple[str, ...] = ()
    notes: str = ""


# REASON: These are the canonical, well-characterized ALD systems used as the
# calibration / regression set. WF6 -> W is the headline test case the user
# asked for. Keep this list factual; novel candidates are scored against the
# patterns these establish.
KNOWN_PRECURSORS: dict[str, KnownPrecursor] = {
    "WF6": KnownPrecursor(
        name="WF6",
        aliases=("tungsten hexafluoride", "tungsten(VI) fluoride"),
        formula="WF6",
        film_element="W",
        vapor_pressure_note="very high; gas/low-boiling liquid (bp ~17 C)",
        bubbler_temp_c=20.0,
        decomposition_onset_c=400.0,
        ald_window_c=(150.0, 350.0),
        common_coreactants=("SiH4", "B2H6", "H2"),
        ligand_class="halide",
        hazards=("toxic", "corrosive", "HF byproduct"),
        notes="Classic W ALD/CVD. SiH4/B2H6 reduce W(VI)->W(0); byproduct HF "
              "can etch oxides/Si, a real integration constraint.",
    ),
    "TMA": KnownPrecursor(
        name="TMA",
        aliases=("trimethylaluminum", "Al(CH3)3", "AlMe3"),
        formula="Al(CH3)3",
        film_element="Al",
        vapor_pressure_note="high; bp ~125 C, strong vapor pressure at RT",
        bubbler_temp_c=20.0,
        decomposition_onset_c=300.0,
        ald_window_c=(150.0, 300.0),
        common_coreactants=("H2O", "O3", "O2 plasma"),
        ligand_class="alkyl",
        hazards=("pyrophoric",),
        notes="The textbook ALD precursor. TMA + H2O -> Al2O3 is the most "
              "self-limiting, well-behaved ALD chemistry known.",
    ),
    "TEMAH": KnownPrecursor(
        name="TEMAH",
        aliases=("tetrakis(ethylmethylamido)hafnium", "Hf(NEtMe)4"),
        formula="Hf[N(C2H5)(CH3)]4",
        film_element="Hf",
        vapor_pressure_note="moderate; heated source ~90-130 C",
        bubbler_temp_c=110.0,
        decomposition_onset_c=250.0,
        ald_window_c=(200.0, 300.0),
        common_coreactants=("H2O", "O3"),
        ligand_class="alkylamide",
        hazards=("moisture sensitive",),
        notes="High-k HfO2 gate dielectric. Alkylamide ligands give clean, "
              "carbon-light films vs. alkoxides; thermal budget limited by "
              "ligand decomposition above ~300 C.",
    ),
    "HfCl4": KnownPrecursor(
        name="HfCl4",
        aliases=("hafnium tetrachloride",),
        formula="HfCl4",
        film_element="Hf",
        vapor_pressure_note="low; solid, sublimes, heated source ~150-200 C",
        bubbler_temp_c=170.0,
        decomposition_onset_c=600.0,
        ald_window_c=(250.0, 500.0),
        common_coreactants=("H2O", "O3"),
        ligand_class="halide",
        hazards=("corrosive", "HCl byproduct"),
        notes="Robust, thermally very stable HfO2 precursor. Solid source and "
              "HCl byproduct (can re-etch/roughen) are the downsides.",
    ),
    "TiCl4": KnownPrecursor(
        name="TiCl4",
        aliases=("titanium tetrachloride",),
        formula="TiCl4",
        film_element="Ti",
        vapor_pressure_note="high; liquid, bp ~136 C",
        bubbler_temp_c=20.0,
        decomposition_onset_c=600.0,
        ald_window_c=(150.0, 450.0),
        common_coreactants=("NH3", "H2O", "H2 plasma"),
        ligand_class="halide",
        hazards=("corrosive", "HCl byproduct", "moisture sensitive"),
        notes="TiN (with NH3) and TiO2 (with H2O). Very stable and volatile; "
              "Cl residue and HCl byproduct are the integration watch-outs.",
    ),
    "TDMAT": KnownPrecursor(
        name="TDMAT",
        aliases=("tetrakis(dimethylamido)titanium", "Ti(NMe2)4"),
        formula="Ti[N(CH3)2]4",
        film_element="Ti",
        vapor_pressure_note="moderate; heated source ~60-75 C",
        bubbler_temp_c=65.0,
        decomposition_onset_c=200.0,
        ald_window_c=(150.0, 220.0),
        common_coreactants=("NH3", "H2O", "N2 plasma"),
        ligand_class="alkylamide",
        hazards=("moisture sensitive",),
        notes="Halide-free TiN/TiO2 route; avoids Cl. Narrow thermal window -- "
              "decomposes ~200 C, so the self-limiting regime is small.",
    ),
    # --- Interconnect-metal precursors (established) for the end-to-end test set ---
    "Ru(EtCp)2": KnownPrecursor(
        name="Ru(EtCp)2",
        aliases=("bis(ethylcyclopentadienyl)ruthenium", "Ru(C7H9)2"),
        formula="Ru(C7H9)2",
        film_element="Ru",
        vapor_pressure_note="moderate; liquid, heated source ~60-90 C",
        bubbler_temp_c=75.0,
        decomposition_onset_c=300.0,
        ald_window_c=(250.0, 350.0),
        common_coreactants=("O2", "O2 plasma", "H2"),
        ligand_class="cyclopentadienyl",
        hazards=("air sensitive",),
        notes="Workhorse Ru interconnect-metal ALD precursor; O2 combusts the Cp "
              "ligands. Carbon residue and nucleation delay are the watch-outs.",
    ),
    "RuCp2": KnownPrecursor(
        name="RuCp2",
        aliases=("ruthenocene", "Ru(C5H5)2"),
        formula="Ru(C5H5)2",
        film_element="Ru",
        vapor_pressure_note="low; solid, sublimes ~100 C",
        bubbler_temp_c=100.0,
        decomposition_onset_c=300.0,
        ald_window_c=(275.0, 350.0),
        common_coreactants=("O2", "O2 plasma"),
        ligand_class="cyclopentadienyl",
        hazards=(),
        notes="Solid ruthenocene; simple but higher sublimation temperature.",
    ),
    "CoCp2": KnownPrecursor(
        name="CoCp2",
        aliases=("cobaltocene", "Co(C5H5)2"),
        formula="Co(C5H5)2",
        film_element="Co",
        vapor_pressure_note="moderate; solid, sublimes ~80-100 C",
        bubbler_temp_c=90.0,
        decomposition_onset_c=250.0,
        ald_window_c=(200.0, 300.0),
        common_coreactants=("NH3", "H2 plasma"),
        ligand_class="cyclopentadienyl",
        hazards=("air sensitive", "pyrophoric"),
        notes="Cobalt interconnect-liner precursor; reductive co-reactant for metal Co.",
    ),
    "MoO2Cl2": KnownPrecursor(
        name="MoO2Cl2",
        aliases=("molybdenum dioxydichloride",),
        formula="MoO2Cl2",
        film_element="Mo",
        vapor_pressure_note="moderate; solid, sublimes ~120-150 C",
        bubbler_temp_c=135.0,
        decomposition_onset_c=400.0,
        ald_window_c=(300.0, 500.0),
        common_coreactants=("H2", "H2 plasma"),
        ligand_class="halide",
        hazards=("corrosive", "HCl byproduct"),
        notes="Oxychloride Mo source for low-resistivity Mo interconnect metal; "
              "avoids the HF of MoF6 while staying volatile.",
    ),
    "Mo(CO)6": KnownPrecursor(
        name="Mo(CO)6",
        aliases=("molybdenum hexacarbonyl",),
        formula="Mo(CO)6",
        film_element="Mo",
        vapor_pressure_note="moderate; solid, sublimes ~40-70 C",
        bubbler_temp_c=55.0,
        decomposition_onset_c=150.0,
        ald_window_c=(100.0, 200.0),
        common_coreactants=("H2 plasma", "O2 plasma"),
        ligand_class="carbonyl",
        hazards=("toxic CO release",),
        notes="Halogen-free Mo carbonyl; very clean (CO leaves) but narrow, low-T "
              "window because it decomposes early.",
    ),
    "B2H6": KnownPrecursor(
        name="B2H6",
        aliases=("diborane",),
        formula="B2H6",
        film_element="B",
        vapor_pressure_note="gas",
        bubbler_temp_c=20.0,
        decomposition_onset_c=300.0,
        ald_window_c=(150.0, 400.0),
        common_coreactants=("WF6",),
        ligand_class="hydride",
        hazards=("toxic", "pyrophoric", "flammable"),
        notes="Reducing co-reactant / nucleation agent for W ALD.",
    ),
}


@dataclass(frozen=True)
class CoReactant:
    name: str
    role: str            # oxidant | reductant | nitridant | etc.
    aggressiveness: float  # 0..1 reactivity/oxidizing strength proxy
    notes: str = ""


CO_REACTANTS: dict[str, CoReactant] = {
    "H2O": CoReactant("H2O", "oxidant", 0.4, "Mild oxidant; standard for oxide ALD."),
    "O3": CoReactant("O3", "oxidant", 0.8, "Strong oxidant; better ligand removal, can over-oxidize substrate."),
    "O2 plasma": CoReactant("O2 plasma", "oxidant", 0.9, "Very reactive; enables low-T but damages soft substrates."),
    "NH3": CoReactant("NH3", "nitridant", 0.5, "Nitride source for TiN/TaN; thermal route needs higher T."),
    "N2 plasma": CoReactant("N2 plasma", "nitridant", 0.8, "Plasma nitridation; low-T nitrides."),
    "H2": CoReactant("H2", "reductant", 0.3, "Mild reductant; often needs plasma or high T."),
    "H2 plasma": CoReactant("H2 plasma", "reductant", 0.7, "Reductive, low-T metal films."),
    "SiH4": CoReactant("SiH4", "reductant", 0.6, "Reduces WF6 -> W; introduces Si, can leave residue."),
    "B2H6": CoReactant("B2H6", "reductant", 0.6, "Reduces WF6 -> W; nucleation layer."),
}


def lookup_precursor(name: str) -> KnownPrecursor | None:
    """Resolve a precursor by name or alias (case-insensitive)."""
    key = name.strip().lower()
    for p in KNOWN_PRECURSORS.values():
        if p.name.lower() == key or key in (a.lower() for a in p.aliases):
            return p
    return None
