from .helpers import quote_payload


def _create_application(user_api, **quote_kwargs):
    quote = user_api.post("/api/v1/quotes", json=quote_payload(**quote_kwargs))
    assert quote.status_code == 201, quote.text
    response = user_api.post(
        "/api/v1/applications",
        json={
            "quote_id": quote.json()["id"],
            "insured_name": "Zhang San",
            "insured_id_no": "110101199001011234",
            "insured_phone": "13800000001",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_application_starts_as_draft(user_api):
    application = _create_application(user_api)
    assert application["status"] == "DRAFT"
    assert application["app_no"].startswith("A")


def test_submit_auto_approve(user_api):
    application = _create_application(user_api)
    response = user_api.post(
        f"/api/v1/applications/{application['id']}/submit"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_submit_manual_review(user_api):
    application = _create_application(
        user_api, product_id=3, sum_insured="500000", term_months=60
    )
    response = user_api.post(
        f"/api/v1/applications/{application['id']}/submit"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "UNDERWRITING"


def test_admin_approve_manual_application(user_api, admin_api):
    application = _create_application(
        user_api, product_id=3, sum_insured="500000", term_months=60
    )
    user_api.post(f"/api/v1/applications/{application['id']}/submit")
    response = admin_api.post(
        f"/api/v1/admin/applications/{application['id']}/underwrite",
        json={"result": "APPROVE", "reason": "manual pass"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_admin_reject_manual_application(user_api, admin_api):
    application = _create_application(
        user_api, product_id=3, sum_insured="500000", term_months=60
    )
    user_api.post(f"/api/v1/applications/{application['id']}/submit")
    response = admin_api.post(
        f"/api/v1/admin/applications/{application['id']}/underwrite",
        json={"result": "REJECT", "reason": "manual reject test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["rejection_reason"] == "manual reject test"


def test_submit_twice_is_conflict(user_api):
    application = _create_application(user_api)
    assert user_api.post(
        f"/api/v1/applications/{application['id']}/submit"
    ).status_code == 200
    response = user_api.post(
        f"/api/v1/applications/{application['id']}/submit"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "APPLICATION_ALREADY_SUBMITTED"


def test_blacklisted_id_is_rejected(user_api):
    quote = user_api.post("/api/v1/quotes", json=quote_payload())
    application = user_api.post(
        "/api/v1/applications",
        json={
            "quote_id": quote.json()["id"],
            "insured_name": "Black List",
            "insured_id_no": "1101011990010000",
            "insured_phone": "13800000009",
        },
    ).json()
    response = user_api.post(
        f"/api/v1/applications/{application['id']}/submit"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_user_cannot_read_others_application(user_api, other_user_api):
    application = _create_application(user_api)
    response = other_user_api.get(f"/api/v1/applications/{application['id']}")
    assert response.status_code == 404
    assert response.json()["code"] == "APPLICATION_NOT_FOUND"
