from datetime import date, timedelta

from app.services.assessment_service import assess_scan
from app.services.decision_service import decide
from app.services.fusion_service import normalize_evidence


def test_fusion_missing_modalities():
    ev = normalize_evidence(vision={"freshness": "fresh", "confidence": 0.8})
    assert ev["modalities_used"] == ["vision"]
    ev2 = normalize_evidence()
    assert ev2["modalities_used"] == []


def test_spoiled_high_voc():
    out = decide(
        vision={"freshness": "spoiled", "confidence": 0.9},
        sensor={"gas_value": 900.0},
        modalities_used=["vision", "sensor"],
    )
    assert out["recommendation"] == "CAUTION_DO_NOT_CONSUME"
    assert any("HIGH_CONCERN" in w for w in out["warnings"])


def test_expired_fresh_vision_expiry_warning():
    out = decide(
        vision={"freshness": "fresh", "confidence": 0.8},
        expiry_date=date.today() - timedelta(days=2),
        modalities_used=["vision", "ocr"],
    )
    assert out["recommendation"] == "CHECK_EXPIRY"
    assert any("EXPIRY_WARNING" in w for w in out["warnings"])


def test_assess_scan_orchestration():
    out = assess_scan(vision={"freshness": "fresh", "confidence": 0.7})
    assert "evidence" in out
    assert out["freshness"] == "fresh"
