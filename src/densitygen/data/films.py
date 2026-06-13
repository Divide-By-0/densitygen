"""Target-film reference data and known-good ALD recipes (the regression set)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Film:
    formula: str
    name: str
    film_element: str          # the element the precursor must deliver
    kind: str                  # oxide | nitride | metal | semiconductor
    role: str                  # what it does in the chip
    typical_coreactants: tuple[str, ...]
    notes: str = ""


FILMS: dict[str, Film] = {
    "W": Film("W", "tungsten", "W", "metal", "low-resistance contact/via/wordline fill",
              ("SiH4", "B2H6", "H2"),
              "Reductive ALD; precursor must be reducible to W(0) and volatile."),
    "Al2O3": Film("Al2O3", "alumina", "Al", "oxide", "dielectric / passivation",
                  ("H2O", "O3", "O2 plasma"),
                  "Most forgiving ALD oxide; wide self-limiting window."),
    "HfO2": Film("HfO2", "hafnia", "Hf", "oxide", "high-k gate dielectric",
                 ("H2O", "O3"),
                 "Thermal budget limited; carbon/Cl residue degrades k and leakage."),
    "TiN": Film("TiN", "titanium nitride", "Ti", "nitride", "diffusion barrier / metal-gate electrode",
                ("NH3", "N2 plasma"),
                "Conductive nitride; needs a nitridant, not an oxidant."),
    "TiO2": Film("TiO2", "titania", "Ti", "oxide", "high-k / optical / catalytic",
                 ("H2O", "O3"), ""),
    "Ru": Film("Ru", "ruthenium", "Ru", "metal", "interconnect liner / metal",
               ("O2", "O2 plasma", "H2"),
               "Hard metal ALD; nucleation and oxidant balance are delicate."),
    "Mo": Film("Mo", "molybdenum", "Mo", "metal", "low-resistance interconnect",
               ("H2", "H2 plasma"), ""),
    "Ta2O5": Film("Ta2O5", "tantalum pentoxide", "Ta", "oxide", "high-k / capacitor dielectric",
                  ("H2O", "O3"), ""),
    # --- Interconnect metals with established precursors (end-to-end test set) ---
    "Co": Film("Co", "cobalt", "Co", "metal", "interconnect liner / cap / fill",
               ("H2", "H2 plasma", "NH3"),
               "Scaled-node liner and low-resistance fill; barrierless candidate."),
    "Ir": Film("Ir", "iridium", "Ir", "metal", "interconnect / electrode",
               ("O2", "O2 plasma", "H2"), "High-MFP metal explored for scaled lines."),
    # --- Emerging interconnect materials WITHOUT mature ALD precursors (design demos) ---
    # These topological semimetals / intermetallics are proposed to beat Cu/W on
    # resistivity at nanoscale (short electron mean free path, barrierless), but
    # have no established single-source ALD precursor -> targets for inverse design.
    "NbP": Film("NbP", "niobium phosphide", "Nb", "semimetal",
                "topological-semimetal interconnect (low nanoscale resistivity)",
                ("PH3", "P plasma"),
                "Weyl semimetal; surface states may carry current with low scattering. "
                "No established ALD precursor -> propose an Nb source."),
    "NbAs": Film("NbAs", "niobium arsenide", "Nb", "semimetal",
                 "topological Weyl-semimetal interconnect candidate",
                 ("AsH3",), "No established ALD route -> propose an Nb source."),
    "MoP": Film("MoP", "molybdenum phosphide", "Mo", "semimetal",
                "low-resistivity interconnect candidate",
                ("PH3",), "Emerging; no mature ALD precursor -> propose an Mo source."),
    "CoSi": Film("CoSi", "cobalt monosilicide", "Co", "intermetallic",
                 "low-resistivity intermetallic interconnect/contact",
                 ("SiH4", "Si2H6"), "No established ALD route -> propose a Co source."),
    "RuO2": Film("RuO2", "ruthenium dioxide", "Ru", "conductive-oxide",
                 "conductive-oxide liner / interconnect candidate",
                 ("O2", "O3", "O2 plasma"), "Conductive oxide; precursor maturity limited."),
}


@dataclass(frozen=True)
class KnownRecipe:
    """A literature-established, working ALD recipe -- used as a regression
    expectation: the screener should rank the canonical precursor at or near
    the top for its film."""

    film: str
    precursor: str
    co_reactant: str
    works: bool = True
    note: str = ""


# REASON: Ground-truth recipes. The test suite asserts the screener ranks the
# canonical precursor #1 for each of these films -- this is how we validate the
# scoring logic against reality instead of against itself.
KNOWN_RECIPES: list[KnownRecipe] = [
    KnownRecipe("W", "WF6", "B2H6", note="Headline test case: WF6 reduced to metallic W."),
    KnownRecipe("W", "WF6", "SiH4", note="Alternative reductant for W ALD."),
    KnownRecipe("Al2O3", "TMA", "H2O", note="Canonical, most self-limiting ALD chemistry."),
    KnownRecipe("HfO2", "TEMAH", "H2O", note="Halide-free high-k gate dielectric."),
    KnownRecipe("HfO2", "HfCl4", "H2O", note="Thermally robust HfO2 route."),
    KnownRecipe("TiN", "TiCl4", "NH3", note="Classic thermal TiN."),
    KnownRecipe("TiN", "TDMAT", "NH3", note="Halide-free TiN."),
]


def lookup_film(name: str) -> Film | None:
    key = name.strip().lower()
    for f in FILMS.values():
        if f.formula.lower() == key or f.name.lower() == key:
            return f
    return None
