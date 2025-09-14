from fastapi import APIRouter
from backend.api.v1 import rbac_api

main_apirouter = APIRouter()
main_apirouter.include_router(rbac_api.rbac_router)


