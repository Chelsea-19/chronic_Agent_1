"""
tests/test_core.py — Lightweight tests for core functionality.
"""
import sys
from pathlib import Path

# Ensure app module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_config_loads():
    """Settings should load without crashing even without secrets."""
    from app.core.config import Settings
    s = Settings()
    assert s.app_name
    assert s.database_url.startswith("sqlite")
    assert isinstance(s.enable_fake_llm, bool)


def test_parser_blood_pressure():
    from app.services.parser import parse_track_message
    result = parse_track_message("[TRACK] 血压 135/88")
    assert result.event_type == "blood_pressure"
    assert result.value_num1 == 135.0
    assert result.value_num2 == 88.0
    assert result.unit == "mmHg"


def test_parser_fasting_glucose():
    from app.services.parser import parse_track_message
    result = parse_track_message("[TRACK] 空腹血糖 6.8")
    assert result.event_type == "fasting_glucose"
    assert result.value_num1 == 6.8


def test_parser_weight():
    from app.services.parser import parse_track_message
    result = parse_track_message("[TRACK] 体重 72.5kg")
    assert result.event_type == "weight"
    assert result.value_num1 == 72.5


def test_meal_risk_detection():
    from app.services.parser import detect_meal_risks
    tags = detect_meal_risks("晚饭喝了全糖奶茶，还吃了两碗米饭")
    assert "高糖饮食" in tags
    assert "高碳水" in tags


def test_meal_risk_low_risk():
    from app.services.parser import detect_meal_risks
    tags = detect_meal_risks("早上吃了水煮蛋加黄瓜")
    assert len(tags) == 0


def test_meal_estimation():
    from app.services.parser import estimate_meal_metrics
    carbs, sodium = estimate_meal_metrics("两碗米饭加奶茶")
    assert carbs > 60  # base 45 + 30 (两碗) + 25 (奶茶) = 100
    assert sodium >= 100


def test_database_init():
    """DB should initialize without errors."""
    from app.core.database import init_db, get_db, PatientProfile

    init_db()
    db = get_db()
    try:
        count = db.query(PatientProfile).count()
        assert count >= 1  # Default patient seeded
    finally:
        db.close()


def test_health_tracking_service():
    """Health tracking should parse and store events."""
    from app.core.database import init_db, get_db
    from app.features.health.service import HealthTrackingService

    init_db()
    db = get_db()
    try:
        service = HealthTrackingService(db, 1)
        event = service.track_from_chat("[TRACK] 血压 142/90")
        assert event.event_type == "blood_pressure"
        assert event.value_num1 == 142.0
    finally:
        db.close()


def test_meal_service():
    """Meal service should analyze and record meals."""
    from app.core.database import init_db, get_db
    from app.features.meals.service import MealService, MealAnalyzeRequest

    init_db()
    db = get_db()
    try:
        service = MealService(db, 1)
        result = service.analyze_and_record(
            MealAnalyzeRequest(description="午餐吃了两碗米饭和红烧肉")
        )
        assert "高碳水" in result["analysis"]["risk_tags"]
        assert "高脂" in result["analysis"]["risk_tags"]
    finally:
        db.close()


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
