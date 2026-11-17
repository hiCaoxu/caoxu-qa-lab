from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..errors import AppError
from ..models import Product, Quote, User
from ..schemas import ProductOut, QuoteOut, QuoteRequest
from ..services.pricing import calculate_premium
from ..utils import generate_no

router = APIRouter(tags=["catalog"])


def _pagination(page: int, page_size: int):
    if page < 1 or page_size < 1 or page_size > 100:
        raise AppError(422, "INVALID_PAGINATION", "Invalid page or page_size")
    return (page - 1) * page_size


@router.get("/products")
def list_products(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
):
    offset = _pagination(page, page_size)
    query = db.query(Product)
    if status:
        query = query.filter(Product.status == status)
    total = query.count()
    items = query.order_by(Product.id.asc()).offset(offset).limit(page_size).all()
    return {
        "items": [ProductOut.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise AppError(404, "PRODUCT_NOT_FOUND", "Product does not exist")
    return product


@router.post("/quotes", response_model=QuoteOut, status_code=201)
def create_quote(
    payload: QuoteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise AppError(404, "PRODUCT_NOT_FOUND", "Product does not exist")
    if product.status != "ON_SALE":
        raise AppError(400, "PRODUCT_NOT_ON_SALE", "Product is not available")

    premium = calculate_premium(
        product, payload.age, payload.sum_insured, payload.term_months
    )
    quote = Quote(
        quote_no=generate_no("Q", db, Quote, "quote_no"),
        user_id=user.id,
        product_id=product.id,
        age=payload.age,
        sum_insured=payload.sum_insured,
        term_months=payload.term_months,
        premium=premium,
        payload={
            "age": payload.age,
            "sum_insured": str(payload.sum_insured),
            "term_months": payload.term_months,
        },
        valid_until=datetime.utcnow() + timedelta(days=30),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.get("/quotes/{quote_id}", response_model=QuoteOut)
def get_quote(
    quote_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Quote).filter(Quote.id == quote_id)
    if user.role != "ADMIN":
        query = query.filter(Quote.user_id == user.id)
    quote = query.first()
    if not quote:
        raise AppError(404, "QUOTE_NOT_FOUND", "Quote does not exist")
    return quote
