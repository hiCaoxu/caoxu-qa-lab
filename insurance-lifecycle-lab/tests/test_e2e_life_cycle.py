from decimal import Decimal

from .helpers import quote_payload


def test_full_insurance_life_cycle(user_api, admin_api):
    quote = user_api.post(
        "/api/v1/quotes",
        json=quote_payload(product_id=3, sum_insured="500000", term_months=60),
    )
    assert quote.status_code == 201
    assert Decimal(str(quote.json()["premium"])) == Decimal("75000.00")

    application = user_api.post(
        "/api/v1/applications",
        json={
            "quote_id": quote.json()["id"],
            "insured_name": "Full Flow User",
            "insured_id_no": "110101199001012345",
            "insured_phone": "13800000005",
        },
    )
    assert application.status_code == 201

    submitted = user_api.post(
        f"/api/v1/applications/{application.json()['id']}/submit"
    )
    assert submitted.json()["status"] == "UNDERWRITING"

    underwritten = admin_api.post(
        f"/api/v1/admin/applications/{application.json()['id']}/underwrite",
        json={"result": "APPROVE", "reason": "manual pass"},
    )
    assert underwritten.json()["status"] == "APPROVED"

    order = user_api.post(
        "/api/v1/payments/orders",
        json={
            "application_id": application.json()["id"],
            "idempotency_key": "e2e-payment-key",
        },
    )
    assert order.status_code == 201

    paid = user_api.post(
        f"/api/v1/payments/orders/{order.json()['id']}/pay",
        json={"result": "SUCCESS"},
    )
    assert paid.json()["status"] == "SUCCESS"

    policies = user_api.get("/api/v1/policies").json()["items"]
    policy = policies[0]
    assert policy["status"] == "ACTIVE"
    assert Decimal(str(policy["sum_insured"])) == Decimal("500000.00")

    endorsement = user_api.post(
        f"/api/v1/policies/{policy['id']}/endorsements",
        json={
            "change_type": "BENEFICIARY",
            "payload": {"beneficiary": "Wang Wu"},
        },
    )
    assert endorsement.status_code == 201
    reviewed_endorsement = admin_api.post(
        f"/api/v1/admin/endorsements/{endorsement.json()['id']}/review",
        json={"result": "APPROVE"},
    )
    assert reviewed_endorsement.json()["status"] == "APPROVED"
    assert (
        user_api.get(f"/api/v1/policies/{policy['id']}").json()["beneficiary"]
        == "Wang Wu"
    )

    claim = user_api.post(
        "/api/v1/claims",
        json={
            "policy_id": policy["id"],
            "incident_date": policy["effective_date"],
            "claim_type": "CRITICAL_ILLNESS",
            "amount": "5000",
            "description": "e2e claim",
        },
    )
    assert claim.status_code == 201
    decided = admin_api.post(
        f"/api/v1/admin/claims/{claim.json()['id']}/decide",
        json={"result": "APPROVE", "approved_amount": "4000"},
    )
    assert decided.json()["status"] == "APPROVED"
    paid_claim = admin_api.post(f"/api/v1/admin/claims/{claim.json()['id']}/pay")
    assert paid_claim.json()["status"] == "PAID"

    surrender = user_api.post(
        f"/api/v1/policies/{policy['id']}/surrender",
        json={"reason": "e2e surrender"},
    )
    assert surrender.status_code == 201
    surrendered = admin_api.post(
        f"/api/v1/admin/surrenders/{surrender.json()['id']}/review",
        json={"result": "APPROVE"},
    )
    assert surrendered.json()["status"] == "APPROVED"

    final_policy = user_api.get(f"/api/v1/policies/{policy['id']}").json()
    assert final_policy["status"] == "SURRENDERED"

    timeline = user_api.get(f"/api/v1/policies/{policy['id']}/timeline").json()
    actions = [item["action"] for item in timeline["items"]]
    assert {"ISSUED", "ENDORSEMENT_APPLIED", "SURRENDER_REVIEWED"}.issubset(actions)
