from decimal import Decimal


def _create_surrender(user_api, policy):
    response = user_api.post(
        f"/api/v1/policies/{policy['id']}/surrender",
        json={"reason": "automation test"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_surrender(user_api, policy):
    surrender = _create_surrender(user_api, policy)
    assert surrender["status"] == "PENDING"
    expected = Decimal(str(policy["premium"])) * Decimal("0.9")
    assert Decimal(str(surrender["refund_amount"])) == expected

    current = user_api.get(f"/api/v1/policies/{policy['id']}").json()
    assert current["status"] == "SURRENDER_PENDING"


def test_admin_approve_surrender(user_api, admin_api, policy):
    surrender = _create_surrender(user_api, policy)
    response = admin_api.post(
        f"/api/v1/admin/surrenders/{surrender['id']}/review",
        json={"result": "APPROVE", "reason": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    current = user_api.get(f"/api/v1/policies/{policy['id']}").json()
    assert current["status"] == "SURRENDERED"


def test_admin_reject_surrender(user_api, admin_api, policy):
    surrender = _create_surrender(user_api, policy)
    response = admin_api.post(
        f"/api/v1/admin/surrenders/{surrender['id']}/review",
        json={"result": "REJECT", "reason": "keep policy"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"

    current = user_api.get(f"/api/v1/policies/{policy['id']}").json()
    assert current["status"] == "ACTIVE"


def test_duplicate_pending_surrender(user_api, policy):
    _create_surrender(user_api, policy)
    response = user_api.post(
        f"/api/v1/policies/{policy['id']}/surrender", json={}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SURRENDER_ALREADY_EXISTS"


def test_claim_after_surrender_is_rejected(user_api, admin_api, policy):
    surrender = _create_surrender(user_api, policy)
    admin_api.post(
        f"/api/v1/admin/surrenders/{surrender['id']}/review",
        json={"result": "APPROVE"},
    )
    response = user_api.post(
        "/api/v1/claims",
        json={
            "policy_id": policy["id"],
            "incident_date": policy["effective_date"],
            "claim_type": "ACCIDENT",
            "amount": "100",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "POLICY_NOT_ACTIVE"
