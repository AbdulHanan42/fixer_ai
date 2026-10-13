import uuid

from app.api.endpoints import ai_diagnosis
from app.db.models import MechanicService, Service
from app.schemas.ai_diagnosis import DiagnosisAnalysis


def test_analyze_matches_only_verified_mechanics_with_exact_service_category(
    client, test_setup, db, monkeypatch
):
    session, _ = db
    test_service = Service(name=f"Diagnosis test {uuid.uuid4().hex}", category="Electrical")
    session.add(test_service)
    session.flush()
    session.add(
        MechanicService(
            mechanic_id=test_setup["mechanic_profile"].id,
            service_id=test_service.id,
            base_price=75.0,
        )
    )
    session.commit()

    async def fake_analyze_image(image_bytes, media_type, description, service_categories):
        assert image_bytes == b"test image"
        assert media_type == "image/jpeg"
        assert "Electrical" in service_categories
        return DiagnosisAnalysis(
            possible_issues=["Alternator or battery issue"],
            urgency="Medium",
            target_service_category="Electrical",
        )

    monkeypatch.setattr(ai_diagnosis, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_diagnosis, "_analyze_image", fake_analyze_image)

    response = client.post(
        "/api/diagnosis/analyze",
        headers={"Authorization": f"Bearer {test_setup['customer_token']}"},
        data={"description": "Dashboard battery light is illuminated."},
        files={"image": ("dashboard.jpg", b"test image", "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ai_diagnosis_results"]["target_service_category"] == "Electrical"
    assert body["ai_diagnosis_results"]["urgency"] == "Medium"
    assert len(body["recommended_mechanics"]) == 1
    assert body["recommended_mechanics"][0]["id"] == str(test_setup["mechanic_profile"].id)
    assert body["recommended_mechanics"][0]["distance_km"] is None

    session.delete(test_service)
    session.commit()
