from fastapi import APIRouter

from .applications import router as applications_router
from .auth import router as auth_router
from .catalog import router as catalog_router
from .claims import router as claims_router
from .payments import router as payments_router
from .policies import router as policies_router
from .surrenders import router as surrenders_router
from .admin import router as admin_router

api_router = APIRouter()

for router in (
    auth_router,
    catalog_router,
    applications_router,
    payments_router,
    policies_router,
    claims_router,
    surrenders_router,
    admin_router,
):
    api_router.include_router(router)
