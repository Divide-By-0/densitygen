from densitygen.chem import parse_formula, FormulaError
import pytest


def test_simple_formula():
    c = parse_formula("WF6")
    assert c.count("W") == 1 and c.count("F") == 6
    assert abs(c.molecular_weight - 297.83) < 0.1


def test_nested_groups():
    c = parse_formula("Al(CH3)3")
    assert c.count("Al") == 1 and c.count("C") == 3 and c.count("H") == 9


def test_bracket_groups():
    # TEMAH: Hf[N(C2H5)(CH3)]4
    c = parse_formula("Hf[N(C2H5)(CH3)]4")
    assert c.count("Hf") == 1
    assert c.count("N") == 4
    assert c.count("C") == 12   # (2+1) carbons per ligand * 4
    assert c.count("H") == 32   # (5+3) H per ligand * 4


def test_film_element_picks_heaviest():
    c = parse_formula("Hf[N(C2H5)(CH3)]4")
    assert c.film_element() == "Hf"


def test_carbon_fraction_and_halogens():
    assert parse_formula("WF6").carbon_fraction == 0.0
    assert parse_formula("WF6").halogens == {"F": 6}


def test_bad_formula_raises():
    with pytest.raises(FormulaError):
        parse_formula("Xq7")
