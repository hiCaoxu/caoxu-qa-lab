from datetime import date, timedelta
from decimal import Decimal

from .helpers import quote_payload


def _create_claim(user_api, policy, amount="1000", incident_date=None, key=None):
    payload = {
        "policy_id": policy["id"],
        "incident_date": incident_date or policy["effective_date"],
        "claim_type": "MEDICAL",
        "amount": amount,
        "description": "automation test claim",
    }
    if key:
        payload["idempotency_key"] = key
    response = user_api.post("/api/v1/claims", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_claim(user_api, policy):
    claim = _create_claim(user_api, policy)
    assert claim["status"] == "SUBMITTED"
    assert claim["claim_no"].startswith("C")


def test_claim_idempotency(user_api, policy):
    first = _create_claim(user_api, policy, key="claim-key-001")
    second = _create_claim(user_api, policy, key="claim-key-001")
    assert second["id"] == first["id"]


def test_claim_before_effective_date(user_api, policy):
    before = date.fromisoformat(policy["effective_date"]) - timedelta(days=1)
    response = user_api.post(
        "/api/v1/claims",
        json={
            "policy_id": policy["id"],
            "incident_date": before.isoformat(),
            "claim_type": "ACCIDENT",
            "amount": "100",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "CLAIM_DATE_OUT_OF_RANGE"


def test_claim_amount_exceeds_sum_insured(user_api, policy):
    too_much = Decimal(str(policy["sum_insured"])) + Decimal("1")
    response = user_api.post(
        "/api/v1/claims",
        json={
            "policy_id": policy["id"],
            "incident_date": policy["effective_date"],
            "claim_type": "ACCIDENT",
            "amount": str(too_much),
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "CLAIM_AMOUNT_EXCEEDS_SUM_INSURED"


def test_admin_approve_and_pay_claim(user_api, admin_api, policy):
    claim = _create_claim(user_api, policy)
    approved = admin_api.post(
        f"/api/v1/admin/claims/{claim['id']}/decide",
        json={
            "result": "APPROVE",
            "approved_amount": "800",
            "reason": "documents verified",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    paid = admin_api.post(f"/api/v1/admin/claims/{claim['id']}/pay")
    assert paid.status_code == 200
    body = paid.json()
    assert body["status"] == "PAID"
    assert Decimal(str(body["approved_amount"])) == Decimal("800.00")


def test_admin_reject_claim(user_api, admin_api, policy):
    claim = _create_claim(user_api, policy)
    response = admin_api.post(
        f"/api/v1/admin/claims/{claim['id']}/decide",
        json={"result": "REJECT", "reason": "not covered"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_other_user_cannot_claim_on_policy(other_user_api, policy):
    response = other_user_api.post(
        "/api/v1/claims",
        json={
            "policy_id": policy["id"],
            "incident_date": policy["effective_date"],
            "claim_type": "ACCIDENT",
            "amount": "100",
        },
    )
    assert response.status_code == 404
    assert response.json()["code"] == "POLICY_NOT_FOUND"
