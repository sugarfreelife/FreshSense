import pytest
from PIL import Image
from pydantic import ValidationError

from app.ml.vision.preprocessing import dark_ratio, load_and_resize
from app.core.config import Settings
from app.core.security import create_access_token, decode_token, get_password_hash, verify_password
from app.core.enums import FreshnessEnum
from app.schemas.assessment import AssessmentRequest
from app.schemas.auth import UserCreate, UserLogin
from app.schemas.sensor import SensorReadingCreate
from app.services.decision_service import decide
from app.utils.files import validate_mime, validate_size


def test_settings_normalize_postgres_alias_and_reject_other_databases():
    settings = Settings(
        DATABASE_URL="postgres://tester:secret@localhost:5432/freshsense",
        JWT_SECRET="test-only-secret-for-freshsense-at-least-32-bytes",
    )
    assert settings.sqlalchemy_url.startswith("postgresql+psycopg2://")
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="sqlite:///freshsense.db", JWT_SECRET="test-only-secret-for-freshsense-at-least-32-bytes")


def test_auth_normalizes_email_and_checks_bcrypt_byte_limit():
    assert UserCreate(email="Tester@Example.com", password="secret1").email == "tester@example.com"
    assert UserLogin(email="TESTER@example.com", password="secret1").email == "tester@example.com"
    with pytest.raises(ValidationError):
        UserCreate(email="tester@example.com", password="🙂" * 20)


def test_password_hashing_and_access_tokens():
    hashed = get_password_hash("secret1")
    assert verify_password("secret1", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("secret1", "not-a-valid-hash")
    assert decode_token(create_access_token("user-id")) == "user-id"
    assert decode_token("invalid-token") is None


def test_zero_vision_confidence_is_preserved():
    result = decide(vision={"freshness": FreshnessEnum.FRESH.value, "confidence": 0.0})
    assert result["confidence"] == 0.0


def test_upload_validation_normalizes_mime_and_enforces_size_limit():
    assert validate_mime("IMAGE/PNG; charset=binary")
    assert not validate_mime(None)
    assert not validate_size(0)
    assert validate_size(10 * 1024 * 1024)
    assert not validate_size(10 * 1024 * 1024 + 1)


def test_sensor_payload_rejects_out_of_range_and_empty_values():
    with pytest.raises(ValidationError):
        SensorReadingCreate(gas_value=5001)
    with pytest.raises(ValidationError):
        SensorReadingCreate(temperature=-41)
    with pytest.raises(ValidationError):
        SensorReadingCreate()
    assert SensorReadingCreate(humidity=100).humidity == 100


def test_assessment_payload_rejects_invalid_freshness_and_confidence():
    with pytest.raises(ValidationError):
        AssessmentRequest(vision_freshness="rotten")
    with pytest.raises(ValidationError):
        AssessmentRequest(vision_confidence=1.1)
    assert AssessmentRequest(vision_freshness="fresh", vision_confidence=0).vision_confidence == 0


def test_vision_resize_does_not_add_black_borders(tmp_path):
    image_path = tmp_path / "bright.png"
    Image.new("RGB", (32, 32), (200, 50, 50)).save(image_path)

    resized = load_and_resize(str(image_path))
    try:
        assert resized.size == (224, 224)
        assert dark_ratio(resized) == 0
    finally:
        resized.close()
