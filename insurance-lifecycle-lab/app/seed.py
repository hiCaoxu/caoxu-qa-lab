from .auth import hash_password
from .database import SessionLocal
from .models import Product, User
from .utils import money

PRODUCTS = [
    {
        "code": "ACC001",
        "name": "安心意外险",
        "type": "ACCIDENT",
        "status": "ON_SALE",
        "min_age": 18,
        "max_age": 60,
        "min_sum_insured": money("10000"),
        "max_sum_insured": money("500000"),
        "auto_approve_limit": money("200000"),
        "base_rate": money("50"),
        "term_options": [12],
    },
    {
        "code": "HLTH001",
        "name": "健康守护医疗险",
        "type": "HEALTH",
        "status": "ON_SALE",
        "min_age": 18,
        "max_age": 55,
        "min_sum_insured": money("10000"),
        "max_sum_insured": money("1000000"),
        "auto_approve_limit": money("300000"),
        "base_rate": money("120"),
        "term_options": [12, 36],
    },
    {
        "code": "CI001",
        "name": "岁月安康重疾险",
        "type": "CRITICAL_ILLNESS",
        "status": "ON_SALE",
        "min_age": 18,
        "max_age": 50,
        "min_sum_insured": money("50000"),
        "max_sum_insured": money("1000000"),
        "auto_approve_limit": money("200000"),
        "base_rate": money("300"),
        "term_options": [60, 120],
    },
]

USERS = [
    {
        "username": "admin",
        "password_hash": hash_password("Admin@123"),
        "role": "ADMIN",
        "full_name": "Lab Admin",
        "phone": "13900000000",
        "id_no": "110101199001019999",
    },
    {
        "username": "demo",
        "password_hash": hash_password("Demo@123"),
        "role": "USER",
        "full_name": "Demo User",
        "phone": "13800000001",
        "id_no": "110101199001011234",
    },
    {
        "username": "demo2",
        "password_hash": hash_password("Demo2@123"),
        "role": "USER",
        "full_name": "Second User",
        "phone": "13800000002",
        "id_no": "110101199001015678",
    },
]


def seed_data():
    db = SessionLocal()
    try:
        for item in PRODUCTS:
            exists = db.query(Product).filter(Product.code == item["code"]).first()
            if not exists:
                db.add(Product(**item))

        for item in USERS:
            exists = db.query(User).filter(User.username == item["username"]).first()
            if not exists:
                db.add(User(**item))

        db.commit()
    finally:
        db.close()
