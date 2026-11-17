def _create_endorsement(user_api, policy_id, change_type="CONTACT", payload=None):
    if payload is None:
        payload = {"phone": "13911112222"}
    response = user_api.post(
        f"/api/v1/policies/{policy_id}/endorsements",
        json={"change_type": change_type, "payload": payload},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_contact_endorsement(user_api, policy):
    endorsement = _create_endorsement(user_api, policy["id"])
    assert endorsement["status"] == "PENDING"
    assert endorsement["endorsement_no"].startswith("E")


def test_create_beneficiary_endorsement(user_api, policy):
    endorsement = _create_endorsement(
        user_api,
        policy["id"],
        change_type="BENEFICIARY",
        payload={"beneficiary": "Li Si"},
    )
    assert endorsement["change_type"] == "BENEFICIARY"
    assert endorsement["payload"]["beneficiary"] == "Li Si"


def test_invalid_contact_payload(user_api, policy):
    response = user_api.post(
        f"/api/v1/policies/{policy['id']}/endorsements",
        json={"change_type": "CONTACT", "payload": {"phone": "123"}},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_CONTACT_PAYLOAD"


def test_admin_approve_contact_change(user_api, admin_api, policy):
    endorsement = _create_endorsement(user_api, policy["id"])
    response = admin_api.post(
        f"/api/v1/admin/endorsements/{endorsement['id']}/review",
        json={"result": "APPROVE", "reason": "contact updated"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    updated = user_api.get(f"/api/v1/policies/{policy['id']}").json()
    assert updated["insured_phone"] == "13911112222"


def test_admin_reject_beneficiary_change(user_api, admin_api, policy):
    endorsement = _create_endorsement(
        user_api,
        policy["id"],
        change_type="BENEFICIARY",
        payload={"beneficiary": "Should Not Apply"},
    )
    response = admin_api.post(
        f"/api/v1/admin/endorsements/{endorsement['id']}/review",
        json={"result": "REJECT", "reason": "not allowed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"

    current = user_api.get(f"/api/v1/policies/{policy['id']}").json()
    assert current["beneficiary"] in ("", None)


def test_non_admin_cannot_review(user_api, policy):
    endorsement = _create_endorsement(user_api, policy["id"])
    response = user_api.post(
        f"/api/v1/admin/endorsements/{endorsement['id']}/review",
        json={"result": "APPROVE"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
