import re
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from densitygen.compute import EnergyResult, MLPotentialClient
from densitygen.schemas import Candidate, ScreeningRequest
from densitygen.screen import screen
from web.app import app


def test_replicate_prediction_metrics_drive_cost(monkeypatch):
    created = []

    class FakePrediction:
        status = "succeeded"

        def wait(self):
            return None

        def dict(self):
            return {
                "id": "pred_123",
                "output": {"energy": -1.25, "forces": [[0.0, 0.0, 0.0]]},
                "metrics": {"predict_time": 2.5, "total_time": 3.2},
            }

    class FakePredictions:
        def create(self, **kwargs):
            created.append(kwargs)
            return FakePrediction()

    class FakeClient:
        def __init__(self, api_token):
            self.api_token = api_token
            self.predictions = FakePredictions()

    monkeypatch.setitem(sys.modules, "replicate", SimpleNamespace(Client=FakeClient))

    client = MLPotentialClient(model="owner/uma-ald", token="tok")
    result = client.energy("1\n\nH 0 0 0\n", task="omol", label="test molecule")
    summary = client.billing_summary()

    assert result.energy_ev == -1.25
    assert created[0]["model"] == "owner/uma-ald"
    assert summary["prediction_count"] == 1
    assert summary["predict_seconds"] == 2.5
    assert summary["estimated_cost_usd"] == 0.0035
    assert summary["calls"][0]["prediction_id"] == "pred_123"


def test_replicate_energy_cache_does_not_double_bill(monkeypatch):
    count = {"n": 0}

    class FakePrediction:
        status = "succeeded"

        def wait(self):
            return None

        def dict(self):
            count["n"] += 1
            return {
                "id": f"pred_{count['n']}",
                "output": {"energy": -2.0, "forces": []},
                "metrics": {"predict_time": 1.0},
            }

    class FakePredictions:
        def create(self, **_kwargs):
            return FakePrediction()

    class FakeClient:
        def __init__(self, api_token):
            self.predictions = FakePredictions()

    monkeypatch.setitem(sys.modules, "replicate", SimpleNamespace(Client=FakeClient))

    client = MLPotentialClient(model="owner/uma-ald", token="tok")
    client.energy("same", task="omol")
    cached = client.energy("same", task="omol")

    assert cached.calls == []
    assert client.billing_summary()["prediction_count"] == 1


def test_web_real_mode_requires_replicate_env(monkeypatch):
    monkeypatch.delenv("DENSITYGEN_UMA_MODEL", raising=False)
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)

    res = TestClient(app).post("/api/screen", json={
        "film": "W",
        "candidates": [{"name": "WF6"}],
        "use_ml_potential": True,
    })

    assert res.status_code == 503
    assert "DENSITYGEN_UMA_MODEL" in res.json()["error"]


def test_web_real_mode_caps_candidate_count():
    res = TestClient(app).post("/api/screen", json={
        "film": "W",
        "candidates": [{"name": f"WCl{i}", "formula": "WCl6"} for i in range(5)],
        "use_ml_potential": True,
    })

    assert res.status_code == 400
    assert "capped" in res.json()["error"]


def test_about_page_keeps_code_snippets_under_ten_lines():
    html = Path("web/static/about.html").read_text()
    code_blocks = re.findall(r"<code>(.*?)</code>", html, flags=re.S)
    code_lines = [
        line for block in code_blocks
        for line in block.strip().splitlines()
        if line.strip()
    ]

    assert len(code_lines) <= 10
    assert "Replicate" in html
    assert "$0.001400/sec" in html


def test_proxy_ml_backend_does_not_claim_uma_confirmation():
    class FakeBackend:
        model = "fake-chgnet"

        def energy_atoms(self, atoms, task="omol", **_kwargs):
            return EnergyResult(-5.0, "chgnet-local", task, note="fake")

        def adsorption_energy_atoms(self, **_kwargs):
            return EnergyResult(-1.0, "chgnet-local", "oc20", note="fake")

    resp = screen(
        ScreeningRequest(
            film="W",
            co_reactant="B2H6",
            candidates=[Candidate(name="WF6")],
            use_ml_potential=True,
        ),
        backend=FakeBackend(),
    )

    assert "incl. UMA" not in resp.ranked_candidates[0].recommended_next_step
    assert "chgnet-local" in resp.ranked_candidates[0].recommended_next_step
