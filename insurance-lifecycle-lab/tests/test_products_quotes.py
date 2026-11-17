from decimal import Decimal

from .helpers import quote_payload


def test_products_list(user_api):
    response = user_api.get("/api/v1/products?page=1&page_size=2")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["page"] == 1


def test_products_filter_on_sale(user_api):
    response = user_api.get("/api/v1/products?status=ON_SALE")
    assert response.status_code == 200
    assert all(item["status"] == "ON_SALE" for item in response.json()["items"])


def test_product_detail(user_api):
    response = user_api.get("/api/v1/products/1")
    assert response.status_code == 200
    assert response.json()["code"] == "ACC001"


def test_product_not_found(user_api):
    response = user_api.get("/api/v1/products/9999")
    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"


def test_quote_success(user_api):
    response = user_api.post("/api/v1/quotes", json=quote_payload())
    assert response.status_code == 201
    body = response.json()
    assert Decimal(str(body["premium"])) == Decimal("500.00")
    assert body["quote_no"].startswith("Q")


def test_quote_age_out_of_range(user_api):
    response = user_api.post("/api/v1/quotes", json=quote_payload(age=17))
    assert response.status_code == 422
    assert response.json()["code"] == "RULE_AGE_OUT_OF_RANGE"


def test_quote_sum_insured_out_of_range(user_api):
    response = user_api.post(
        "/api/v1/quotes", json=quote_payload(sum_insured="600000")
    )
    assert response.status_code == 422
    assert response.json()["code"] == "RULE_SUM_INSURED_OUT_OF_RANGE"


def test_quote_invalid_term(user_api):
    response = user_api.post("/api/v1/quotes", json=quote_payload(term_months=24))
    assert response.status_code == 422
    assert response.json()["code"] == "RULE_TERM_INVALID"


def test_quote_requires_auth(api):
    response = api.post("/api/v1/quotes", json=quote_payload())
    assert response.status_code == 401
