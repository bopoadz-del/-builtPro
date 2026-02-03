from __future__ import annotations

import types


def test_analytics_engine_delegates(monkeypatch):
    import backend.services.analytics_engine as mod

    dummy = types.SimpleNamespace(query_logs=lambda project_id, query: f"OK {project_id}:{query}")
    monkeypatch.setattr(mod, "analytics_service", dummy, raising=True)

    # context project_id should override message project_id
    res = mod.handle_analytics_engine({"project_id": "msg", "content": "hello"}, {"project_id": "ctx"})
    assert res["service"] == "analytics_engine"
    assert res["result"] == "OK ctx:hello"


def test_analytics_engine_handles_missing_service(monkeypatch):
    import backend.services.analytics_engine as mod

    monkeypatch.setattr(mod, "analytics_service", None, raising=True)
    res = mod.handle_analytics_engine({"content": "hello"}, {"project_id": "p"})
    assert res["service"] == "analytics_engine"
    assert "error occurred" in res["result"].lower()


def test_consolidated_takeoff_delegates(monkeypatch):
    import backend.services.consolidated_takeoff as mod

    dummy = types.SimpleNamespace(run_consolidation=lambda project_id, query: f"TAKEOFF {project_id}:{query}")
    monkeypatch.setattr(mod, "takeoff_service", dummy, raising=True)

    res = mod.handle_consolidated_takeoff({"project_id": "p1", "text": "do takeoff"}, {})
    assert res["service"] == "consolidated_takeoff"
    assert res["result"] == "TAKEOFF p1:do takeoff"


def test_consolidated_takeoff_handles_missing_service(monkeypatch):
    import backend.services.consolidated_takeoff as mod

    monkeypatch.setattr(mod, "takeoff_service", None, raising=True)
    res = mod.handle_consolidated_takeoff("anything", {"project_id": "p"})
    assert res["service"] == "consolidated_takeoff"
    assert "error occurred" in res["result"].lower()
