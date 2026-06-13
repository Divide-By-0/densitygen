"""DensityGen: ML-accelerated ALD precursor screening for chemists.

Public API:
    from densitygen import screen, ScreeningRequest, Candidate
    resp = screen(ScreeningRequest(film="W", candidates=[Candidate(name="WF6")],
                                   co_reactant="B2H6"))
    print(resp.ranked_candidates[0].overall_score)
"""

from densitygen.schemas import (
    Candidate,
    CandidateResult,
    ScreeningRequest,
    ScreeningResponse,
)
from densitygen.screen import screen

__version__ = "0.1.0"
__all__ = [
    "screen",
    "Candidate",
    "CandidateResult",
    "ScreeningRequest",
    "ScreeningResponse",
    "__version__",
]
