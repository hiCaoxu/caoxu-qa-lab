from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..errors import AppError
from ..models import Claim, Policy, User
from ..schemas import ClaimCreateRequest, ClaimOut
from ..utils import add_audit, generate_no

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(
    payload: ClaimCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.idempotency_key:
        existing = db.query(Claim).filter(
            Claim.idempotency_key == payload.idempotency_key
        ).first()
        if existing:
            if existing.user_id != user.id or existing.policy_id != payload.policy_id:
                raise AppError(409, "IDEMPOTENCY_CONFLICT", "Idempotency key already used")
            return existing

    policy = db.query(Policy).filter(
        Policy.id == payload.policy_id, Policy.user_id == user.id
    ).first()
    if not policy:
        raise AppError(404, "POLICY_NOT_FOUND", "Policy does not exist")
    if policy.status != "ACTIVE":
        raise AppError(422, "POLICY_NOT_ACTIVE", "Only an active policy can accept claims")

    if not (policy.effective_date <= payload.incident_date <= policy.expiry_date):
        raise AppError(
            422,
            "CLAIM_DATE_OUT_OF_RANGE",
            "Incident date is outside the policy coverage period",
        )

    amount = Decimal(str(payload.amount))
    if amount <= 0:
        raise AppError(422, "INVALID_CLAIM_AMOUNT", "Claim amount must be positive")
    if amount > policy.sum_insured:
        raise AppError(
            422,
            "CLAIM_AMOUNT_EXCEEDS_SUM_INSURED",
            "Claim amount exceeds the insured sum",
        )

    claim = Claim(
        claim_no=generate_no("C", db, Claim, "claim_no"),
        policy_id=policy.id,
        user_id=user.id,
        incident_date=payload.incident_date,
        claim_type=payload.claim_type,
        amount=amount,
        description=payload.description,
        status="SUBMITTED",
        idempotency_key=payload.idempotency_key,
        approved_amount=Decimal("0"),
    )
    db.add(claim)
    db.flush()
    add_audit(db, "CLAIM", claim.id, "CREATED", None, "SUBMITTED", user.username)
    db.commit()
    db.refresh(claim)
    return claim


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(
    claim_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Claim).filter(Claim.id == claim_id)
    if user.role != "ADMIN":
        query = query.filter(Claim.user_id == user.id)
    claim = query.first()
    if not claim:
        raise AppError(404, "CLAIM_NOT_FOUND", "Claim does not exist")
    return claim


@router.get("")
def list_claims(
    policy_id: int = None,
    status: str = None,
    page: int = 1,
    page_size: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 100:
        raise AppError(422, "INVALID_PAGINATION", "Invalid page or page_size")
    query = db.query(Claim)
    if user.role != "ADMIN":
        query = query.filter(Claim.user_id == user.id)
    if policy_id:
        query = query.filter(Claim.policy_id == policy_id)
    if status:
        query = query.filter(Claim.status == status)
    total = query.count()
    items = (
        query.order_by(Claim.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [ClaimOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
