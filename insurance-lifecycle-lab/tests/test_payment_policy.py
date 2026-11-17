from decimal import Decimal

from .helpers import create_approved_application


def _order(user_api, admin_api, idempotency_key=None):
    application = create_approved_application(user_api, admin_api)
    payload = {"application_id": application["id"]}
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    response = user_api.post("/api/v1/payments/orders", json=payload)
    assert response.status_code == 201, response.text
    return application, response.json()


def test_create_payment_order(user_api, admin_api):
    application, order = _order(user_api, admin_api)
    assert order["application_id"] == application["id"]
    assert order["status"] == "INIT"
    assert Decimal(str(order["amount"])) == Decimal("500.00")


def test_idempotent_order_creation(user_api, admin_api):
    _, first = _order(user_api, admin_api, idempotency_key="same-key-001")
    application = create_approved_application(user_api, admin_api)
    response = user_api.post(
        "/api/v1/payments/orders",
        json={
            "application_id": application["id"],
            "idempotency_key": "same-key-001",
        },
    )
    assert response.status_code == 409


def test_idempotent_key_returns_same_order(user_api, admin_api):
    application, first = _order(user_api, admin_api, idempotency_key="same-key-002")
    response = user_api.post(
        "/api/v1/payments/orders",
        json={
            "application_id": application["id"],
            "idempotency_key": "same-key-002",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == first["id"]


def test_failed_payment_then_success(user_api, admin_api):
    application, order = _order(user_api, admin_api)
    failed = user_api.post(
        f"/api/v1/payments/orders/{order['id']}/pay", json={"result": "FAILED"}
    )
    assert failed.status_code == 200
    assert failed.json()["status"] == "FAILED"

    current_app = user_api.get(f"/api/v1/applications/{application['id']}").json()
    assert current_app["status"] == "PAYING"

    paid = user_api.post(
        f"/api/v1/payments/orders/{order['id']}/pay", json={"result": "SUCCESS"}
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "SUCCESS"

    policies = user_api.get("/api/v1/policies").json()
    assert policies["total"] == 1
    assert policies["items"][0]["status"] == "ACTIVE"


def test_duplicate_success_payment_is_idempotent(policy_context, user_api):
    order_id = policy_context["order"]["id"]
    response = user_api.post(
        f"/api/v1/payments/orders/{order_id}/pay", json={"result": "SUCCESS"}
    )
    assert response.status_code == 200
    assert user_api.get("/api/v1/policies").json()["total"] == 1


def test_callback_requires_token(api):
    response = api.post(
        "/api/v1/payments/callback",
        json={
            "order_no": "PO000000000000",
            "result": "SUCCESS",
            "transaction_id": "txn-requires-token",
        },
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CALLBACK_TOKEN"


def test_callback_issues_policy(user_api, admin_api, api):
    _, order = _order(user_api, admin_api)
    response = api.post(
        "/api/v1/payments/callback",
        json={
            "order_no": order["order_no"],
            "result": "SUCCESS",
            "transaction_id": "txn-callback-001",
        },
        headers={"X-Callback-Token": "test-callback-token"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert user_api.get("/api/v1/policies").json()["total"] == 1


def test_policy_timeline(policy_context, user_api):
    policy_id = policy_context["policy"]["id"]
    response = user_api.get(f"/api/v1/policies/{policy_id}/timeline")
    assert response.status_code == 200
    actions = [item["action"] for item in response.json()["items"]]
    assert "ISSUED" in actions
