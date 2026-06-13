"""Request/response schemas. These are the stable contract the CLI, the
Replicate `predict.py`, and any future MCP tool all share."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Candidate(BaseModel):
    """A precursor candidate to screen. Identify it by at least one of:
    a known name, a molecular formula, or a SMILES string."""

    name: str = Field(..., description="Human label / known precursor name")
    formula: Optional[str] = Field(None, description="Molecular formula, e.g. 'Al(CH3)3'")
    smiles: Optional[str] = Field(None, description="SMILES (converted via RDKit if available)")

    @model_validator(mode="after")
    def _need_identifier(self) -> "Candidate":
        if not (self.formula or self.smiles or self.name):
            raise ValueError("candidate needs a name, formula, or smiles")
        return self


class ScreeningRequest(BaseModel):
    film: str = Field(..., description="Target film, e.g. 'W', 'Al2O3', 'HfO2', 'TiN'")
    candidates: list[Candidate] = Field(..., min_length=1)
    co_reactant: Optional[str] = Field(None, description="e.g. 'H2O', 'O3', 'NH3', 'B2H6'")
    surface: Optional[str] = Field(None, description="Free-text surface/integration context")
    temperature_max_c: Optional[float] = Field(
        None, description="Process temperature ceiling in Celsius (thermal budget)"
    )
    forbidden_elements: list[str] = Field(
        default_factory=list, description="Elements that must not enter the chamber/film"
    )
    use_ml_potential: bool = Field(
        False,
        description="If true, call the hosted UMA model on Replicate for real "
        "atomistic energies. If false, run the fast local descriptor scorer only.",
    )


class ScoreComponent(BaseModel):
    name: str
    score: float = Field(..., ge=0.0, le=1.0)
    evidence: str
    confidence: Literal["measured", "estimated", "unknown"] = "estimated"


class SimulationCall(BaseModel):
    label: str
    task: str
    model: str
    prediction_id: Optional[str] = None
    predict_time_s: float = 0.0
    total_time_s: float = 0.0
    cost_usd: float = 0.0


class BillingSummary(BaseModel):
    hardware: str = "gpu-a100-large"
    rate_usd_per_second: float = 0.0014
    prediction_count: int = 0
    predict_seconds: float = 0.0
    estimated_cost_usd: float = 0.0
    calls: list[SimulationCall] = Field(default_factory=list)


class CandidateResult(BaseModel):
    name: str
    formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    film_element: Optional[str] = None
    overall_score: float = Field(..., ge=0.0, le=1.0)
    components: list[ScoreComponent]
    warnings: list[str] = Field(default_factory=list)
    recommended_next_step: str = ""
    is_known_recipe: bool = False
    origin: Literal["input", "proposed"] = "input"
    ml_energy_ev: Optional[float] = None  # real UMA energy when computed
    ml_calls: list[SimulationCall] = Field(default_factory=list)


class ModelProvenance(BaseModel):
    compute_backend: str  # "local-descriptors" | "uma-replicate" | ...
    model_name: Optional[str] = None
    replicate_model: Optional[str] = None
    notes: str = ""


class ScreeningResponse(BaseModel):
    film: str
    co_reactant: Optional[str] = None
    ranked_candidates: list[CandidateResult]
    warnings: list[str] = Field(default_factory=list)
    model_provenance: ModelProvenance
    billing: Optional[BillingSummary] = None
