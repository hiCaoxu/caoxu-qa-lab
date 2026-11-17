from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..errors import AppError
from ..models import AuditLog, Endorsement, Policy, User
from ..schemas import (
    AuditLogOut,
    EndorsementCreateRequest,
    EndorsementOut,
    PolicyOut,
)
from ..utils import add_audit, generate_no

router = APIRouter(tags=["policies"])


def _owned_policy(policy_id, user, db):
    query = db.query(Policy).filter(Policy.id == policy_id)
    if user.role != "ADMIN":
        query = query.filter(Policy.user_id == user.id)
    policy = query.first()
    if not policy:
        raise AppError(404, "POLICY_NOT_FOUND", "Policy does not exist")
    return policy


@router.get("/policies")
def list_policies(
    status: str = None,
    page: int = 1,
    page_size: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 100:
        raise AppError(422, "INVALID_PAGINATION", "Invalid page or page_size")
    query = db.query(Policy)
    if user.role != "ADMIN":
        query = query.filter(Policy.user_id == user.id)
    if status:
        query = query.filter(Policy.status == status)
    total = query.count()
    items = (
        query.order_by(Policy.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [PolicyOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/policies/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _owned_policy(policy_id, user, db)


@router.get("/policies/{policy_id}/timeline")
def policy_timeline(
    policy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_policy(policy_id, user, db)
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "POLICY", AuditLog.entity_id == policy_id)
        .order_by(AuditLog.id.asc())
        .all()
    )
    return {
        "items": [AuditLogOut.model_validate(log) for log in logs],
        "total": len(logs),
    }


@router.post("/policies/{policy_id}/endorsements", response_model=EndorsementOut, status_code=201)
def create_endorsement(
    policy_id: int,
    payload: EndorsementCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policy = _owned_policy(policy_id, user, db)
    if policy.status != "ACTIVE":
        raise AppError(409, "POLICY_NOT_ACTIVE", "Only an active policy can be endorsed")

    if payload.change_type == "CONTACT":
        phone = str(payload.payload.get("phone", ""))
        if len(phone) != 11 or not phone.isdigit():
            raise AppError(422, "INVALID_CONTACT_PAYLOAD", "A valid 11-digit phone is required")
    elif payload.change_type == "BENEFICIARY":
        beneficiary = str(payload.payload.get("beneficiary", "")).strip()
        if not beneficiary:
            raise AppError(
                422,
                "INVALID_BENEFICIARY_PAYLOAD",
                "Beneficiary name is required",
            )
    else:
        raise AppError(422, "UNSUPPORTED_CHANGE_TYPE", "Unsupported endorsement type")

    endorsement = Endorsement(
        endorsement_no=generate_no("E", db, Endorsement, "endorsement_no"),
        policy_id=policy.id,
        user_id=user.id,
        change_type=payload.change_type,
        payload=payload.payload,
        status="PENDING",
    )
    db.add(endorsement)
    db.flush()
    add_audit(
        db,
        "ENDORSEMENT",
        endorsement.id,
        "CREATED",
        None,
        "PENDING",
        user.username,
    )
    db.commit()
    db.refresh(endorsement)
    return endorsement


@router.get("/policies/{policy_id}/endorsements")
def list_endorsements(
    policy_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_policy(policy_id, user, db)
    items = (
        db.query(Endorsement)
        .filter(Endorsement.policy_id == policy_id)
        .order_by(Endorsement.id.desc())
        .all()
    )
    return {
        "items": [EndorsementOut.model_validate(item) for item in items],
        "total": len(items),
    }


@router.get("/endorsements/{endorsement_id}", response_model=EndorsementOut)
def get_endorsement(
    endorsement_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Endorsement).filter(Endorsement.id == endorsement_id)
    if user.role != "ADMIN":
        query = query.filter(Endorsement.user_id == user.id)
    endorsement = query.first()
    if not endorsement:
        raise AppError(404, "ENDORSEMENT_NOT_FOUND", "Endorsement does not exist")
    return endorsement
