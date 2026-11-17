from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = "Tester"
    phone: str = "13800000000"
    id_no: str = "110101199001011234"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class UserOut(ORMModel):
    id: int
    username: str
    role: str
    full_name: str
    phone: str
    id_no: str
    created_at: datetime


class ProductOut(ORMModel):
    id: int
    code: str
    name: str
    type: str
    status: str
    min_age: int
    max_age: int
    min_sum_insured: Decimal
    max_sum_insured: Decimal
    auto_approve_limit: Decimal
    base_rate: Decimal
    term_options: List[int]


class QuoteRequest(BaseModel):
    product_id: int
    age: int
    sum_insured: Decimal
    term_months: int


class QuoteOut(ORMModel):
    id: int
    quote_no: str
    user_id: int
    product_id: int
    age: int
    sum_insured: Decimal
    term_months: int
    premium: Decimal
    payload: Dict[str, Any]
    valid_until: datetime


class ApplicationCreateRequest(BaseModel):
    quote_id: int
    insured_name: str
    insured_id_no: str
    insured_phone: str


class ApplicationOut(ORMModel):
    id: int
    app_no: str
    user_id: int
    quote_id: int
    product_id: int
    insured_name: str
    insured_id_no: str
    insured_phone: str
    age: int
    sum_insured: Decimal
    term_months: int
    premium: Decimal
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UnderwriteRequest(BaseModel):
    result: Literal["APPROVE", "REJECT"]
    reason: Optional[str] = None


class PaymentOrderCreateRequest(BaseModel):
    application_id: int
    idempotency_key: Optional[str] = None


class PayRequest(BaseModel):
    result: Literal["SUCCESS", "FAILED"]


class PaymentCallbackRequest(BaseModel):
    order_no: str
    result: Literal["SUCCESS", "FAILED"]
    transaction_id: str


class PaymentOrderOut(ORMModel):
    id: int
    order_no: str
    application_id: int
    user_id: int
    amount: Decimal
    status: str
    idempotency_key: Optional[str] = None
    callback_txn: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PolicyOut(ORMModel):
    id: int
    policy_no: str
    application_id: int
    user_id: int
    product_id: int
    insured_name: str
    insured_id_no: str
    insured_phone: str
    beneficiary: Optional[str] = None
    sum_insured: Decimal
    premium: Decimal
    term_months: int
    status: str
    effective_date: date
    expiry_date: date
    created_at: datetime
    updated_at: datetime


class EndorsementCreateRequest(BaseModel):
    change_type: Literal["CONTACT", "BENEFICIARY"]
    payload: Dict[str, Any]


class ReviewRequest(BaseModel):
    result: Literal["APPROVE", "REJECT"]
    reason: Optional[str] = None


class EndorsementOut(ORMModel):
    id: int
    endorsement_no: str
    policy_id: int
    user_id: int
    change_type: str
    payload: Dict[str, Any]
    status: str
    reviewed_by: Optional[str] = None
    review_note: Optional[str] = None
    effective_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ClaimCreateRequest(BaseModel):
    policy_id: int
    incident_date: date
    claim_type: str
    amount: Decimal
    description: str = ""
    idempotency_key: Optional[str] = None


class ClaimDecideRequest(BaseModel):
    result: Literal["APPROVE", "REJECT"]
    approved_amount: Optional[Decimal] = None
    reason: Optional[str] = None


class ClaimOut(ORMModel):
    id: int
    claim_no: str
    policy_id: int
    user_id: int
    incident_date: date
    claim_type: str
    amount: Decimal
    description: Optional[str] = None
    status: str
    idempotency_key: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_note: Optional[str] = None
    approved_amount: Decimal
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SurrenderCreateRequest(BaseModel):
    reason: Optional[str] = None


class SurrenderOut(ORMModel):
    id: int
    surrender_no: str
    policy_id: int
    user_id: int
    refund_amount: Decimal
    reason: Optional[str] = None
    status: str
    reviewed_by: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AuditLogOut(ORMModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    operator: str
    detail: Dict[str, Any]
    created_at: datetime
