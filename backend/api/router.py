from fastapi import APIRouter
from backend.api.v1.rbac import rbac_router



main_apirouter = APIRouter()
main_apirouter.include_router(rbac_router, tags=["RBAC"])


