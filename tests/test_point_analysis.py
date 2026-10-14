import csv
import json

import pytest
from fastapi.testclient import TestClient

import main
from routers import point_analysis as router
from services import point_analysis_service as service


def test_score_requires_logic_counterfactual_and_verified_citations():
    point = {"Device": "D1", "Name": "Safety door", "Address": "I0.0", "Type": "Input"}
    identity = {**point, "address": "I0.0", "name": "Safety door"}

    insufficient = service.score_point(point, identity, citations_verified=True)
    assert insufficient["验证状态"] == "资料不足"
    assert insufficient["重要性评分"] == 5

    item = {
        **identity,
        "critical_path_level": 5,
        "gate_level": 5,
        "safety_level": 5,
        "logic_references": [{"source_file": "logic.scl", "location": "Network 1", "quote": "I0.0 AND M1.0 => Q0.0"}],
        "downstream_outputs": ["Q0.0", "Q0.1", "Q0.2", "Q0.3", "Q0.4", "Q0.5", "Q0.6", "Q0.7"],
        "operating_gates": ["g1", "g2", "g3", "g4", "g5"],
        "counterfactual_cases": [{"changed": True}],
        "evidence": [{"source_file": "logic.scl", "location": "Network 1", "quote": "I0.0 AND M1.0 => Q0.0"}],
    }
    reviewer = {"review_status": "accepted"}
    verified = service.score_point(point, item, reviewer, citations_verified=True)
    unverified = service.score_point(point, item, reviewer, citations_verified=False)
    unreviewed = service.score_point(point, item, None, citations_verified=True)
    assert verified["重要性评分"] >= 70
    assert verified["验证状态"] == "已验证"
    assert unverified["验证状态"] == "高优先级候选"
    assert unreviewed["验证状态"] == "高优先级候选"


def test_citation_verification_checks_source_file_quote_and_location(tmp_path):
    source = tmp_path / "logic.scl"
    source.write_text("Network 1: I0.0 AND M1.0 => Q0.0;", encoding="utf-8")
    citation = {"source_file": "logic.scl", "location": "Network 1", "quote": "I0.0 AND M1.0 => Q0.0"}
    assert service._citation_is_real(tmp_path, citation)
    assert not service._citation_is_real(tmp_path, {**citation, "quote": "invented logic string"})
    assert not service._citation_is_real(tmp_path, {**citation, "source_file": "../logic.scl"})
    assert not service._citation_is_real(tmp_path, {**citation, "location": ""})


def test_upload_results_filter_paging_download_and_safe_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(router, "POINT_ANALYSIS_DIR", tmp_path)

    async def fake_analysis(run_id, input_dir):
        rows = [
            {"Device": f"D{i}", "Name": f"Point {i}", "Address": f"I{i}.0", "Type": "Input",
             "重要性等级": "候选-高优先级" if i == 2 else "资料不足",
             "重要性评分": i, "验证状态": "高优先级候选" if i == 2 else "资料不足",
             "证据等级": "D", "验证结论": "测试", "证据定位": "", "details": {} }
            for i in range(3)
        ]
        run = service.load_run(run_id)
        run.update(status="completed", progress=1, summary={"total": 3, "verified": 0,
                    "high_priority_candidates": 1, "insufficient": 2, "readable_logic_files": 0},
                    result_count=3, warnings=[])
        service.save_run(run_id, run)
        service._write_csv(run_id, rows)
        (service.run_path(run_id) / "results.json").write_text(
            json.dumps({"run_id": run_id, "summary": run["summary"], "rows": rows}), encoding="utf-8")

    monkeypatch.setattr(router.analysis, "run_analysis", fake_analysis)
    with TestClient(main.app) as client:
        response = client.post("/api/v1/point-analysis/runs", files=[
            ("files", ("PLC点位表.csv", "Device,Name,Address,Type\nD1,Sensor,I0.0,Input\n", "text/csv")),
            ("files", ("Project/logic.scl", "Network 1", "text/plain")),
        ])
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        status = client.get(f"/api/v1/point-analysis/runs/{run_id}")
        assert status.json()["status"] == "completed"

        results = client.get(f"/api/v1/point-analysis/runs/{run_id}/results?page=2&page_size=1")
        assert results.status_code == 200
        assert results.json()["total"] == 3
        assert results.json()["rows"][0]["Device"] == "D1"

        filtered = client.get(f"/api/v1/point-analysis/runs/{run_id}/results", params={"status": "高优先级候选", "search": "Point 2"})
        assert filtered.json()["total"] == 1
        assert filtered.json()["rows"][0]["Address"] == "I2.0"

        downloaded = client.get(f"/api/v1/point-analysis/runs/{run_id}/download")
        assert downloaded.status_code == 200
        assert "Device,Name,Address,Type" in downloaded.content.decode("utf-8-sig")

        invalid = client.post("/api/v1/point-analysis/runs", files=[
            ("files", ("../outside.csv", "Device,Name,Address,Type\n", "text/csv")),
        ])
        assert invalid.status_code == 400
        assert not (tmp_path.parent / "outside.csv").exists()


@pytest.mark.parametrize("filename", ["../outside.csv", "C:/outside.csv", "\\\\server\\share.csv", ""])
def test_upload_path_rejects_absolute_and_traversal(filename):
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        router._relative_upload_path(filename)
