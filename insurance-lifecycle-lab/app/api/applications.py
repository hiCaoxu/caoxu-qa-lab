from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..errors import AppError
from ..models import Application, Product, Quote, UnderwritingRecord, User
from ..schemas import ApplicationCreateRequest, ApplicationOut
from ..services.state_machine import ensure_transition
from ..services.underwriting import auto_underwrite
from ..utils import add_audit, generate_no

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quote = db.query(Quote).filter(
        Quote.id == payload.quote_id, Quote.user_id == user.id
    ).first()
    if not quote:
        raise AppError(404, "QUOTE_NOT_FOUND", "Quote does not exist")
    if quote.valid_until < datetime.utcnow():
        raise AppError(400, "QUOTE_EXPIRED", "Quote has expired")

    product = db.query(Product).filter(Product.id == quote.product_id).first()
    if not product or product.status != "ON_SALE":
        raise AppError(400, "PRODUCT_UNAVAILABLE", "Product is no longer available")

    if not payload.insured_name.strip():
        raise AppError(422, "INVALID_INSURED_NAME", "Insured name is required")
    if len(payload.insured_id_no) < 6:
        raise AppError(422, "INVALID_INSURED_ID_NO", "Insured ID number is too short")
    if len(payload.insured_phone) < 7:
        raise AppError(422, "INVALID_INSURED_PHONE", "Insured phone is too short")

    application = Application(
        app_no=generate_no("A", db, Application, "app_no"),
        user_id=user.id,
        quote_id=quote.id,
        product_id=product.id,
        insured_name=payload.insured_name.strip(),
        insured_id_no=payload.insured_id_no,
        insured_phone=payload.insured_phone,
        age=quote.age,
        sum_insured=quote.sum_insured,
        term_months=quote.term_months,
        premium=quote.premium,
        status="DRAFT",
    )
    db.add(application)
    db.flush()
    add_audit(
        db,
        "APPLICATION",
        application.id,
        "CREATED",
        None,
        "DRAFT",
        user.username,
    )
    db.commit()
    db.refresh(application)
    return application


@router.post("/{app_id}/submit", response_model=ApplicationOut)
def submit_application(
    app_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.query(Application).filter(
        Application.id == app_id, Application.user_id == user.id
    ).first()
    if not application:
        raise AppError(404, "APPLICATION_NOT_FOUND", "Application does not exist")

    if application.status != "DRAFT":
        raise AppError(
            409,
            "APPLICATION_ALREADY_SUBMITTED",
            "Only a draft application can be submitted",
        )

    ensure_transition("APPLICATION", "DRAFT", "SUBMITTED")
    application.status = "SUBMITTED"
    add_audit(db, "APPLICATION", application.id, "SUBMITTED", "DRAFT", "SUBMITTED", user.username)

    ensure_transition("APPLICATION", "SUBMITTED", "UNDERWRITING")
    application.status = "UNDERWRITING"
    add_audit(
        db,
        "APPLICATION",
        application.id,
        "UNDERWRITING_STARTED",
        "SUBMITTED",
        "UNDERWRITING",
        "SYSTEM",
    )

    product = db.query(Product).filter(Product.id == application.product_id).first()
    result, reason, mode = auto_underwrite(application, product)

    if result in ("APPROVED", "REJECTED"):
        ensure_transition("APPLICATION", "UNDERWRITING", result)
        application.status = result
        add_audit(
            db,
            "APPLICATION",
            application.id,
            "AUTO_UNDERWRITTEN",
            "UNDERWRITING",
            result,
            "SYSTEM",
            {"reason": reason},
        )
        if result == "REJECTED":
            application.rejection_reason = reason

    db.add(
        UnderwritingRecord(
            application_id=application.id,
            reviewer="SYSTEM",
            result=result,
            reason=reason,
            mode=mode,
        )
    )
    application.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return application


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(
    app_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Application).filter(Application.id == app_id)
    if user.role != "ADMIN":
        query = query.filter(Application.user_id == user.id)
    application = query.first()
    if not application:
        raise AppError(404, "APPLICATION_NOT_FOUND", "Application does not exist")
    return application


@router.get("")
def list_applications(
    status: str = None,
    page: int = 1,
    page_size: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 100:
        raise AppError(422, "INVALID_PAGINATION", "Invalid page or page_size")
    query = db.query(Application)
    if user.role != "ADMIN":
        query = query.filter(Application.user_id == user.id)
    if status:
        query = query.filter(Application.status == status)
    total = query.count()
    items = (
        query.order_by(Application.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [ApplicationOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
