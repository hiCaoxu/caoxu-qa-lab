from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..errors import AppError
from ..models import Policy, Surrender, User
from ..schemas import SurrenderCreateRequest, SurrenderOut
from ..services.state_machine import ensure_transition
from ..utils import add_audit, generate_no, money, months_between

router = APIRouter(tags=["surrenders"])


def _owned_policy(policy_id, user, db):
    query = db.query(Policy).filter(Policy.id == policy_id)
    if user.role != "ADMIN":
        query = query.filter(Policy.user_id == user.id)
    policy = query.first()
    if not policy:
        raise AppError(404, "POLICY_NOT_FOUND", "Policy does not exist")
    return policy


@router.post("/policies/{policy_id}/surrender", response_model=SurrenderOut, status_code=201)
def create_surrender(
    policy_id: int,
    payload: SurrenderCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = _owned_policy(policy_id, user, db)
    existing = db.query(Surrender).filter(
        Surrender.policy_id == policy.id, Surrender.status == "PENDING"
    ).first()
    if existing:
        raise AppError(409, "SURRENDER_ALREADY_EXISTS", "A pending surrender already exists")

    if policy.status != "ACTIVE":
        raise AppError(409, "POLICY_NOT_ACTIVE", "Only an active policy can be surrendered")

    remaining = max(months_between(date.today(), policy.expiry_date), 0)
    refund = money(
        Decimal(str(policy.premium))
        * Decimal(remaining)
        / Decimal(str(policy.term_months))
        * Decimal("0.9")
    )

    surrender = Surrender(
        surrender_no=generate_no("S", db, Surrender, "surrender_no"),
        policy_id=policy.id,
        user_id=user.id,
        refund_amount=refund,
        reason=payload.reason or "",
        status="PENDING",
    )
    db.add(surrender)
    db.flush()
    add_audit(
        db,
        "SURRENDER",
        surrender.id,
        "CREATED",
        None,
        "PENDING",
        user.username,
    )

    ensure_transition("POLICY", "ACTIVE", "SURRENDER_PENDING")
    policy.status = "SURRENDER_PENDING"
    add_audit(
        db,
        "POLICY",
        policy.id,
        "SURRENDER_REQUESTED",
        "ACTIVE",
        "SURRENDER_PENDING",
        user.username,
    )

    db.commit()
    db.refresh(surrender)
    return surrender


@router.get("/surrenders/{surrender_id}", response_model=SurrenderOut)
def get_surrender(
    surrender_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Surrender).filter(Surrender.id == surrender_id)
    if user.role != "ADMIN":
        query = query.filter(Surrender.user_id == user.id)
    surrender = query.first()
    if not surrender:
        raise AppError(404, "SURRENDER_NOT_FOUND", "Surrender does not exist")
    return surrender


@router.get("/policies/{policy_id}/surrenders")
def list_surrenders(
    policy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_policy(policy_id, user, db)
    items = (
        db.query(Surrender)
        .filter(Surrender.policy_id == policy_id)
        .order_by(Surrender.id.desc())
        .all()
    )
    return {
        "items": [SurrenderOut.model_validate(item) for item in items],
        "total": len(items),
    }
