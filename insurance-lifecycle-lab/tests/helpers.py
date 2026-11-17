def quote_payload(product_id=1, age=30, sum_insured="100000", term_months=12):
    return {
        "product_id": product_id,
        "age": age,
        "sum_insured": sum_insured,
        "term_months": term_months,
    }


def create_approved_application(
    user_api,
    admin_api,
    product_id=1,
    sum_insured="100000",
    term_months=12,
    insured_id_no="110101199001011234",
):
    quote = user_api.post(
        "/api/v1/quotes",
        json=quote_payload(product_id, 30, sum_insured, term_months),
    )
    assert quote.status_code == 201, quote.text

    application = user_api.post(
        "/api/v1/applications",
        json={
            "quote_id": quote.json()["id"],
            "insured_name": "Zhang San",
            "insured_id_no": insured_id_no,
            "insured_phone": "13800000001",
        },
    )
    assert application.status_code == 201, application.text

    submitted = user_api.post(
        f"/api/v1/applications/{application.json()['id']}/submit"
    )
    assert submitted.status_code == 200, submitted.text
    data = submitted.json()

    if data["status"] == "UNDERWRITING":
        reviewed = admin_api.post(
            f"/api/v1/admin/applications/{data['id']}/underwrite",
            json={"result": "APPROVE", "reason": "manual review passed"},
        )
        assert reviewed.status_code == 200, reviewed.text
        data = reviewed.json()

    assert data["status"] == "APPROVED", data
    return data


def issue_policy(user_api, admin_api, **kwargs):
    application = create_approved_application(user_api, admin_api, **kwargs)
    order = user_api.post(
        "/api/v1/payments/orders",
        json={
            "application_id": application["id"],
            "idempotency_key": f"idem-{application['id']}",
        },
    )
    assert order.status_code == 201, order.text

    paid = user_api.post(
        f"/api/v1/payments/orders/{order.json()['id']}/pay",
        json={"result": "SUCCESS"},
    )
    assert paid.status_code == 200, paid.text

    policies = user_api.get("/api/v1/policies").json()["items"]
    assert policies, "A policy should have been issued"

    return {
        "application": application,
        "order": order.json(),
        "payment": paid.json(),
        "policy": policies[0],
    }
