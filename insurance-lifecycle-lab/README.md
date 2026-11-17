# InsureLab - Insurance Lifecycle API Playground

A deliberately small but realistic insurance API service built for practicing black-box API automation with `pytest + requests`.

No real payment gateway or third-party service is involved. Payment, underwriting, and approvals are simulated inside the app so that every test is deterministic and repeatable.

## 1. Quick start

```bash
cd D:/Data/caoxu-qa-lab/insurance-lifecycle-lab
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>
- Health check: <http://127.0.0.1:8000/health>

On Windows you can also double-click `run_server.bat`.

## 2. Seed accounts

The database is seeded automatically on startup.

| Username | Password | Role | Notes |
|---|---|---|---|
| `admin` | `Admin@123` | `ADMIN` | Reviews underwriting, endorsements, claims, surrenders |
| `demo` | `Demo@123` | `USER` | Regular user |
| `demo2` | `Demo2@123` | `USER` | Used for cross-user authorization tests |

Seed products:

| Code | Name | Type | Terms | Auto approve limit |
|---|---|---|---|---|
| `ACC001` | 安心意外险 | `ACCIDENT` | 12m | 200000 |
| `HLTH001` | 健康守护医疗险 | `HEALTH` | 12/36m | 300000 |
| `CI001` | 岁月安康重疾险 | `CRITICAL_ILLNESS` | 60/120m | 200000 |

## 3. Run automated tests

```bash
python -m pytest
```

If a globally installed pytest plugin conflicts with this environment, disable plugin autoloading:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
```

PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest
```

Generate an HTML report:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p pytest_metadata.plugin -p pytest_html.plugin --html=reports/report.html --self-contained-html
```

PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest -p pytest_metadata.plugin -p pytest_html.plugin --html=reports/report.html --self-contained-html
```

On Windows you can double-click `run_tests.bat`.

The test suite starts its own uvicorn process on a random free port with a temporary SQLite database. It does **not** touch your local `data/insurelab.db`.

## 4. API map

All business endpoints are under `/api/v1`.

### Auth

| Method | Path |
|---|---|
| POST | `/auth/register` |
| POST | `/auth/login` |
| GET | `/auth/me` |

### Catalog and quote

| Method | Path |
|---|---|
| GET | `/products` |
| GET | `/products/{product_id}` |
| POST | `/quotes` |
| GET | `/quotes/{quote_id}` |

### Application and underwriting

| Method | Path |
|---|---|
| POST | `/applications` |
| POST | `/applications/{app_id}/submit` |
| GET | `/applications/{app_id}` |
| GET | `/applications` |
| POST | `/admin/applications/{app_id}/underwrite` |

### Payment and policy

| Method | Path |
|---|---|
| POST | `/payments/orders` |
| POST | `/payments/orders/{order_id}/pay` |
| GET | `/payments/orders/{order_id}` |
| POST | `/payments/callback` |
| GET | `/policies` |
| GET | `/policies/{policy_id}` |
| GET | `/policies/{policy_id}/timeline` |

The callback endpoint requires header `X-Callback-Token`. Default value is `callback-secret`, configurable through the `CALLBACK_TOKEN` environment variable.

### Endorsement, claim, surrender

| Method | Path |
|---|---|
| POST | `/policies/{policy_id}/endorsements` |
| GET | `/policies/{policy_id}/endorsements` |
| GET | `/endorsements/{endorsement_id}` |
| POST | `/admin/endorsements/{id}/review` |
| POST | `/claims` |
| GET | `/claims/{claim_id}` |
| GET | `/claims` |
| POST | `/admin/claims/{id}/decide` |
| POST | `/admin/claims/{id}/pay` |
| POST | `/policies/{policy_id}/surrender` |
| GET | `/surrenders/{surrender_id}` |
| GET | `/policies/{policy_id}/surrenders` |
| POST | `/admin/surrenders/{id}/review` |

## 5. State machines

Application:

```text
DRAFT -> SUBMITTED -> UNDERWRITING -> APPROVED -> PAYING -> POLICY_ISSUED
                                  \-> REJECTED
```

Payment order:

```text
INIT -> SUCCESS
INIT -> FAILED -> SUCCESS
```

Policy:

```text
ACTIVE -> SURRENDER_PENDING -> SURRENDERED
                           \-> ACTIVE
```

Claim:

```text
SUBMITTED -> REVIEWING -> APPROVED -> PAID
                       \-> REJECTED
```

Endorsement / surrender:

```text
PENDING -> APPROVED
PENDING -> REJECTED
```

Illegal transitions return HTTP `409` with code `INVALID_STATE_TRANSITION`.

## 6. Business rules worth testing

- Premium: `base_rate * (sum_insured / 10000) * (term_months / 12) * age_factor`
  - `age_factor`: `<=30 -> 1.0`, `31-40 -> 1.1`, `41-50 -> 1.25`, `>50 -> 1.5`
- Auto underwriting:
  - insured ID ending with `0000` is blacklisted and rejected
  - sum insured above `auto_approve_limit` requires manual review
- Payment order creation supports `idempotency_key`
- Claim submission supports `idempotency_key`
- Claim date must be inside the policy coverage period
- Claim amount must be positive and must not exceed the insured sum
- Refund: `premium * remaining_months / total_months * 0.9`
- Only `ACTIVE` policies can be endorsed, claimed against, or surrendered

## 7. Unified error format

```json
{
  "code": "RULE_AGE_OUT_OF_RANGE",
  "message": "Age must be between 18 and 60",
  "details": {}
}
```

Common codes:

| Code | HTTP |
|---|---|
| `UNAUTHENTICATED` / `INVALID_TOKEN` | 401 |
| `FORBIDDEN` | 403 |
| `VALIDATION_ERROR` | 422 |
| `INVALID_STATE_TRANSITION` | 409 |
| `IDEMPOTENCY_CONFLICT` | 409 |
| `POLICY_NOT_ACTIVE` | 422 / 409 |

## 8. Project layout

```text
insurance-lifecycle-lab/
  app/
    api/          HTTP routers
    services/     pricing, underwriting, state machine
    main.py       FastAPI app
    models.py     SQLAlchemy models
    schemas.py    Pydantic request/response models
    seed.py       products and users
  tests/
    conftest.py   live-server fixture and login fixtures
    client.py     requests wrapper
    helpers.py    flow builders
    test_*.py     API automation cases
  requirements.txt
  pytest.ini
  README.md
```
