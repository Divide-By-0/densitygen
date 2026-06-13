"""Curated reference data: known precursors, co-reactants, films, recipes."""

from densitygen.data.films import (
    FILMS,
    KNOWN_RECIPES,
    Film,
    KnownRecipe,
    lookup_film,
)
from densitygen.data.precursors import (
    CO_REACTANTS,
    KNOWN_PRECURSORS,
    CoReactant,
    KnownPrecursor,
    lookup_precursor,
)

__all__ = [
    "FILMS", "KNOWN_RECIPES", "Film", "KnownRecipe", "lookup_film",
    "CO_REACTANTS", "KNOWN_PRECURSORS", "CoReactant", "KnownPrecursor",
    "lookup_precursor",
]
