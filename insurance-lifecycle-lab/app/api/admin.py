from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..database import get_db
from ..errors import AppError
from ..models import (
    Application,
    Claim,
    Endorsement,
    Policy,
    Surrender,
    UnderwritingRecord,
    User,
)
from ..schemas import (
    ApplicationOut,
    ClaimDecideRequest,
    ClaimOut,
    EndorsementOut,
    ReviewRequest,
    SurrenderOut,
    UnderwriteRequest,
)
from ..services.state_machine import ensure_transition
from ..utils import add_audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/applications/{app_id}/underwrite", response_model=ApplicationOut)
def underwrite_application(
    app_id: int,
    payload: UnderwriteRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise AppError(404, "APPLICATION_NOT_FOUND", "Application does not exist")
    if application.status != "UNDERWRITING":
        raise AppError(
            409,
            "APPLICATION_NOT_IN_UNDERWRITING",
            "Application is not waiting for manual underwriting",
        )

    target = "APPROVED" if payload.result == "APPROVE" else "REJECTED"
    previous = application.status
    ensure_transition("APPLICATION", previous, target)
    application.status = target
    reason = payload.reason or ("MANUAL_APPROVED" if target == "APPROVED" else "MANUAL_REJECTED")
    if target == "REJECTED":
        application.rejection_reason = reason
    application.updated_at = datetime.utcnow()

    db.add(
        UnderwritingRecord(
            application_id=application.id,
            reviewer=admin.username,
            result=target,
            reason=reason,
            mode="MANUAL",
        )
    )
    add_audit(
        db,
        "APPLICATION",
        application.id,
        "MANUAL_UNDERWRITTEN",
        previous,
        target,
        admin.username,
        {"reason": reason},
    )
    db.commit()
    db.refresh(application)
    return application


@router.post("/endorsements/{endorsement_id}/review", response_model=EndorsementOut)
def review_endorsement(
    endorsement_id: int,
    payload: ReviewRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    endorsement = db.query(Endorsement).filter(Endorsement.id == endorsement_id).first()
    if not endorsement:
        raise AppError(404, "ENDORSEMENT_NOT_FOUND", "Endorsement does not exist")
    if endorsement.status != "PENDING":
        raise AppError(409, "ENDORSEMENT_NOT_PENDING", "Endorsement is already reviewed")

    target = "APPROVED" if payload.result == "APPROVE" else "REJECTED"
    previous = endorsement.status
    ensure_transition("ENDORSEMENT", previous, target)
    endorsement.status = target
    endorsement.reviewed_by = admin.username
    endorsement.review_note = payload.reason or ""
    endorsement.updated_at = datetime.utcnow()

    if target == "APPROVED":
        policy = db.query(Policy).filter(Policy.id == endorsement.policy_id).first()
        if not policy:
            raise AppError(404, "POLICY_NOT_FOUND", "Policy does not exist")
        if endorsement.change_type == "CONTACT":
            phone = endorsement.payload.get("phone")
            if phone:
                policy.insured_phone = str(phone)
        elif endorsement.change_type == "BENEFICIARY":
            beneficiary = endorsement.payload.get("beneficiary")
            if beneficiary:
                policy.beneficiary = str(beneficiary)
        endorsement.effective_at = datetime.utcnow()
        add_audit(
            db,
            "POLICY",
            policy.id,
            "ENDORSEMENT_APPLIED",
            None,
            None,
            admin.username,
            {"endorsement_id": endorsement.id, "change_type": endorsement.change_type},
        )

    add_audit(
        db,
        "ENDORSEMENT",
        endorsement.id,
        "REVIEWED",
        previous,
        target,
        admin.username,
    )
    db.commit()
    db.refresh(endorsement)
    return endorsement


@router.post("/claims/{claim_id}/decide", response_model=ClaimOut)
def decide_claim(
    claim_id: int,
    payload: ClaimDecideRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise AppError(404, "CLAIM_NOT_FOUND", "Claim does not exist")

    if claim.status == "SUBMITTED":
        ensure_transition("CLAIM", "SUBMITTED", "REVIEWING")
        claim.status = "REVIEWING"
        add_audit(db, "CLAIM", claim.id, "REVIEW_STARTED", "SUBMITTED", "REVIEWING", admin.username)
    if claim.status != "REVIEWING":
        raise AppError(409, "CLAIM_NOT_REVIEWABLE", "Claim is not waiting for review")

    target = "APPROVED" if payload.result == "APPROVE" else "REJECTED"
    ensure_transition("CLAIM", "REVIEWING", target)

    if target == "APPROVED":
        approved = (
            payload.approved_amount
            if payload.approved_amount is not None
            else claim.amount
        )
        approved = Decimal(str(approved))
        if approved <= 0 or approved > claim.amount:
            raise AppError(422, "INVALID_APPROVED_AMOUNT", "Approved amount is invalid")
        claim.approved_amount = approved
    else:
        claim.approved_amount = Decimal("0")

    claim.status = target
    claim.reviewed_by = admin.username
    claim.review_note = payload.reason or ""
    claim.updated_at = datetime.utcnow()
    add_audit(db, "CLAIM", claim.id, "DECIDED", "REVIEWING", target, admin.username)
    db.commit()
    db.refresh(claim)
    return claim


@router.post("/claims/{claim_id}/pay", response_model=ClaimOut)
def pay_claim(
    claim_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise AppError(404, "CLAIM_NOT_FOUND", "Claim does not exist")
    if claim.status != "APPROVED":
        raise AppError(409, "CLAIM_NOT_PAYABLE", "Only an approved claim can be paid")

    previous = claim.status
    ensure_transition("CLAIM", previous, "PAID")
    claim.status = "PAID"
    claim.paid_at = datetime.utcnow()
    claim.updated_at = datetime.utcnow()
    add_audit(db, "CLAIM", claim.id, "PAID", previous, "PAID", admin.username)
    db.commit()
    db.refresh(claim)
    return claim


@router.post("/surrenders/{surrender_id}/review", response_model=SurrenderOut)
def review_surrender(
    surrender_id: int,
    payload: ReviewRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    surrender = db.query(Surrender).filter(Surrender.id == surrender_id).first()
    if not surrender:
        raise AppError(404, "SURRENDER_NOT_FOUND", "Surrender does not exist")
    if surrender.status != "PENDING":
        raise AppError(409, "SURRENDER_NOT_PENDING", "Surrender is already reviewed")

    target = "APPROVED" if payload.result == "APPROVE" else "REJECTED"
    previous = surrender.status
    ensure_transition("SURRENDER", previous, target)
    surrender.status = target
    surrender.reviewed_by = admin.username
    surrender.review_note = payload.reason or ""
    surrender.updated_at = datetime.utcnow()

    policy = db.query(Policy).filter(Policy.id == surrender.policy_id).first()
    if not policy:
        raise AppError(404, "POLICY_NOT_FOUND", "Policy does not exist")

    policy_target = "SURRENDERED" if target == "APPROVED" else "ACTIVE"
    if policy.status == "SURRENDER_PENDING":
        ensure_transition("POLICY", "SURRENDER_PENDING", policy_target)
        add_audit(
            db,
            "POLICY",
            policy.id,
            "SURRENDER_REVIEWED",
            "SURRENDER_PENDING",
            policy_target,
            admin.username,
        )
        policy.status = policy_target
        policy.updated_at = datetime.utcnow()

    add_audit(db, "SURRENDER", surrender.id, "REVIEWED", previous, target, admin.username)
    db.commit()
    db.refresh(surrender)
    return surrender
