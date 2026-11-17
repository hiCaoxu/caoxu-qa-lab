from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import CALLBACK_TOKEN
from ..database import get_db
from ..errors import AppError
from ..models import Application, PaymentOrder, Policy, User
from ..schemas import (
    PayRequest,
    PaymentCallbackRequest,
    PaymentOrderCreateRequest,
    PaymentOrderOut,
)
from ..services.state_machine import ensure_transition
from ..utils import add_audit, add_months, generate_no

router = APIRouter(prefix="/payments", tags=["payments"])


def verify_callback_token(x_callback_token: str = Header(default="")):
    if x_callback_token != CALLBACK_TOKEN:
        raise AppError(401, "INVALID_CALLBACK_TOKEN", "Invalid callback token")


def _apply_payment_result(db: Session, order: PaymentOrder, result: str, operator: str):
    previous = order.status
    if previous == "SUCCESS":
        return order

    if result == "SUCCESS":
        ensure_transition("PAYMENT", previous, "SUCCESS")
        order.status = "SUCCESS"
        order.paid_at = datetime.utcnow()
        add_audit(db, "PAYMENT", order.id, "PAY_SUCCESS", previous, "SUCCESS", operator)

        application = db.query(Application).filter(
            Application.id == order.application_id
        ).first()
        if application and application.status != "POLICY_ISSUED":
            app_previous = application.status
            ensure_transition("APPLICATION", app_previous, "POLICY_ISSUED")
            application.status = "POLICY_ISSUED"
            add_audit(
                db,
                "APPLICATION",
                application.id,
                "POLICY_ISSUED",
                app_previous,
                "POLICY_ISSUED",
                operator,
            )

            existing_policy = db.query(Policy).filter(
                Policy.application_id == application.id
            ).first()
            if not existing_policy:
                effective_date = date.today()
                policy = Policy(
                    policy_no=generate_no("P", db, Policy, "policy_no"),
                    application_id=application.id,
                    user_id=application.user_id,
                    product_id=application.product_id,
                    insured_name=application.insured_name,
                    insured_id_no=application.insured_id_no,
                    insured_phone=application.insured_phone,
                    beneficiary="",
                    sum_insured=application.sum_insured,
                    premium=application.premium,
                    term_months=application.term_months,
                    status="ACTIVE",
                    effective_date=effective_date,
                    expiry_date=add_months(effective_date, application.term_months),
                )
                db.add(policy)
                db.flush()
                add_audit(db, "POLICY", policy.id, "ISSUED", None, "ACTIVE", operator)
    else:
        ensure_transition("PAYMENT", previous, "FAILED")
        order.status = "FAILED"
        add_audit(db, "PAYMENT", order.id, "PAY_FAILED", previous, "FAILED", operator)

    return order


@router.post("/orders", response_model=PaymentOrderOut, status_code=201)
def create_payment_order(
    payload: PaymentOrderCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.idempotency_key:
        existing = db.query(PaymentOrder).filter(
            PaymentOrder.idempotency_key == payload.idempotency_key
        ).first()
        if existing:
            if (
                existing.user_id != user.id
                or existing.application_id != payload.application_id
            ):
                raise AppError(409, "IDEMPOTENCY_CONFLICT", "Idempotency key already used")
            return existing

    application = db.query(Application).filter(
        Application.id == payload.application_id, Application.user_id == user.id
    ).first()
    if not application:
        raise AppError(404, "APPLICATION_NOT_FOUND", "Application does not exist")
    if application.status != "APPROVED":
        raise AppError(
            409,
            "APPLICATION_NOT_PAYABLE",
            f"Application is not payable, current status: {application.status}",
        )

    ensure_transition("APPLICATION", "APPROVED", "PAYING")
    application.status = "PAYING"
    add_audit(
        db,
        "APPLICATION",
        application.id,
        "PAYMENT_STARTED",
        "APPROVED",
        "PAYING",
        user.username,
    )

    order = PaymentOrder(
        order_no=generate_no("PO", db, PaymentOrder, "order_no"),
        application_id=application.id,
        user_id=user.id,
        amount=Decimal(str(application.premium)),
        status="INIT",
        idempotency_key=payload.idempotency_key,
    )
    db.add(order)
    db.flush()
    add_audit(db, "PAYMENT", order.id, "CREATED", None, "INIT", user.username)
    db.commit()
    db.refresh(order)
    return order


@router.post("/orders/{order_id}/pay", response_model=PaymentOrderOut)
def pay_order(
    order_id: int,
    payload: PayRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(PaymentOrder).filter(
        PaymentOrder.id == order_id, PaymentOrder.user_id == user.id
    ).first()
    if not order:
        raise AppError(404, "PAYMENT_ORDER_NOT_FOUND", "Payment order does not exist")

    _apply_payment_result(db, order, payload.result, user.username)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders/{order_id}", response_model=PaymentOrderOut)
def get_payment_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(PaymentOrder).filter(PaymentOrder.id == order_id)
    if user.role != "ADMIN":
        query = query.filter(PaymentOrder.user_id == user.id)
    order = query.first()
    if not order:
        raise AppError(404, "PAYMENT_ORDER_NOT_FOUND", "Payment order does not exist")
    return order


@router.post(
    "/callback",
    response_model=PaymentOrderOut,
    dependencies=[Depends(verify_callback_token)],
)
def payment_callback(payload: PaymentCallbackRequest, db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(
        PaymentOrder.order_no == payload.order_no
    ).first()
    if not order:
        raise AppError(404, "PAYMENT_ORDER_NOT_FOUND", "Payment order does not exist")

    if order.callback_txn:
        if order.callback_txn == payload.transaction_id:
            return order
        raise AppError(409, "CALLBACK_TXN_CONFLICT", "Transaction id already used")

    order.callback_txn = payload.transaction_id
    _apply_payment_result(db, order, payload.result, "PAYMENT_GATEWAY")
    db.commit()
    db.refresh(order)
    return order
