from sqlalchemy import Column, Date, DateTime, Integer, JSON, Numeric, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), default="USER", nullable=False)
    full_name = Column(String(64), default="")
    phone = Column(String(32), default="")
    id_no = Column(String(64), default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False)
    status = Column(String(16), default="ON_SALE", nullable=False)
    min_age = Column(Integer, nullable=False)
    max_age = Column(Integer, nullable=False)
    min_sum_insured = Column(Numeric(12, 2), nullable=False)
    max_sum_insured = Column(Numeric(12, 2), nullable=False)
    auto_approve_limit = Column(Numeric(12, 2), nullable=False)
    base_rate = Column(Numeric(12, 2), nullable=False)
    term_options = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote_no = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    sum_insured = Column(Numeric(12, 2), nullable=False)
    term_months = Column(Integer, nullable=False)
    premium = Column(Numeric(12, 2), nullable=False)
    payload = Column(JSON, default=dict)
    valid_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    app_no = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    quote_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    insured_name = Column(String(64), nullable=False)
    insured_id_no = Column(String(64), nullable=False)
    insured_phone = Column(String(32), nullable=False)
    age = Column(Integer, nullable=False)
    sum_insured = Column(Numeric(12, 2), nullable=False)
    term_months = Column(Integer, nullable=False)
    premium = Column(Numeric(12, 2), nullable=False)
    status = Column(String(24), default="DRAFT", nullable=False, index=True)
    rejection_reason = Column(String(255), default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class UnderwritingRecord(Base):
    __tablename__ = "underwriting_records"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=False, index=True)
    reviewer = Column(String(64), default="SYSTEM", nullable=False)
    result = Column(String(24), nullable=False)
    reason = Column(String(255), default="")
    mode = Column(String(16), default="AUTO", nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(32), unique=True, index=True, nullable=False)
    application_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(16), default="INIT", nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=True)
    callback_txn = Column(String(128), unique=True, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_no = Column(String(32), unique=True, index=True, nullable=False)
    application_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    insured_name = Column(String(64), nullable=False)
    insured_id_no = Column(String(64), nullable=False)
    insured_phone = Column(String(32), nullable=False)
    beneficiary = Column(String(64), default="")
    sum_insured = Column(Numeric(12, 2), nullable=False)
    premium = Column(Numeric(12, 2), nullable=False)
    term_months = Column(Integer, nullable=False)
    status = Column(String(24), default="ACTIVE", nullable=False, index=True)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Endorsement(Base):
    __tablename__ = "endorsements"

    id = Column(Integer, primary_key=True, index=True)
    endorsement_no = Column(String(32), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    change_type = Column(String(32), nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String(16), default="PENDING", nullable=False, index=True)
    reviewed_by = Column(String(64), default="")
    review_note = Column(String(255), default="")
    effective_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_no = Column(String(32), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    incident_date = Column(Date, nullable=False)
    claim_type = Column(String(32), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(500), default="")
    status = Column(String(16), default="SUBMITTED", nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=True)
    reviewed_by = Column(String(64), default="")
    review_note = Column(String(255), default="")
    approved_amount = Column(Numeric(12, 2), default=0, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Surrender(Base):
    __tablename__ = "surrenders"

    id = Column(Integer, primary_key=True, index=True)
    surrender_no = Column(String(32), unique=True, index=True, nullable=False)
    policy_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    refund_amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), default="")
    status = Column(String(16), default="PENDING", nullable=False, index=True)
    reviewed_by = Column(String(64), default="")
    review_note = Column(String(255), default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(32), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(64), nullable=False)
    from_status = Column(String(24), nullable=True)
    to_status = Column(String(24), nullable=True)
    operator = Column(String(64), default="SYSTEM", nullable=False)
    detail = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
